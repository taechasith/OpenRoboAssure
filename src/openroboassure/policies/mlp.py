"""A small deterministic NumPy policy-gradient MLP for CPU-first P06 runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

FloatMatrix = npt.NDArray[np.float64]

_OBSERVATION_SCALE = np.array(
    [0.25, 0.20, 0.30, 0.25, 0.20, 0.10, 0.25, 0.20, 0.30, 1.0], dtype=np.float64
)


@dataclass(frozen=True)
class PolicySpecification:
    """The P06-gated architecture and exploration parameters."""

    observation_size: int = 10
    action_size: int = 4
    hidden_layers: tuple[int, int] = (64, 64)
    exploration_std: float = 0.35
    learning_rate: float = 0.002

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible immutable architecture description."""
        return asdict(self)


@dataclass(frozen=True)
class PolicySample:
    """One stochastic policy decision and cached activations for REINFORCE."""

    features: FloatMatrix
    hidden_one: FloatMatrix
    hidden_two: FloatMatrix
    mean: FloatMatrix
    noise: FloatMatrix
    action: FloatMatrix


class StateMlpPolicy:
    """Two-hidden-layer state-only MLP trained with episodic REINFORCE.

    This deliberately small implementation avoids hidden accelerator, cloud, and
    framework-dependent behaviour. Every baseline receives this exact model,
    reward handling, action transform, and update rule.
    """

    def __init__(self, seed: int, specification: PolicySpecification | None = None) -> None:
        self.specification = specification or PolicySpecification()
        self._rng = np.random.default_rng(seed)
        first, second = self.specification.hidden_layers
        self.weight_one = self._initialise(self.specification.observation_size, first)
        self.bias_one = np.zeros(first, dtype=np.float64)
        self.weight_two = self._initialise(first, second)
        self.bias_two = np.zeros(second, dtype=np.float64)
        self.weight_out = self._initialise(second, self.specification.action_size)
        self.bias_out = np.zeros(self.specification.action_size, dtype=np.float64)

    def _initialise(self, inputs: int, outputs: int) -> FloatMatrix:
        limit = np.sqrt(6.0 / (inputs + outputs))
        return self._rng.uniform(-limit, limit, size=(inputs, outputs)).astype(np.float64)

    def act(self, observation: FloatMatrix) -> FloatMatrix:
        """Return the deterministic bounded action used for evaluation."""
        _, _, _, mean = self._forward(observation)
        return np.tanh(mean)

    def sample(self, observation: FloatMatrix) -> PolicySample:
        """Draw one bounded exploration action and retain its score-function cache."""
        features, hidden_one, hidden_two, mean = self._forward(observation)
        noise = self._rng.normal(0.0, 1.0, size=mean.shape).astype(np.float64)
        action = np.tanh(mean + self.specification.exploration_std * noise)
        return PolicySample(features, hidden_one, hidden_two, mean, noise, action)

    def update(self, samples: list[PolicySample], rewards: list[float]) -> float:
        """Apply one normalized episodic REINFORCE update and return its return."""
        if len(samples) != len(rewards) or not samples:
            raise ValueError("Policy update requires one non-empty reward for every sample")
        returns = np.cumsum(np.asarray(rewards, dtype=np.float64)[::-1])[::-1]
        advantages = returns - returns.mean()
        standard_deviation = float(advantages.std())
        if standard_deviation > 1e-12:
            advantages /= standard_deviation

        grad_weight_one = np.zeros_like(self.weight_one)
        grad_bias_one = np.zeros_like(self.bias_one)
        grad_weight_two = np.zeros_like(self.weight_two)
        grad_bias_two = np.zeros_like(self.bias_two)
        grad_weight_out = np.zeros_like(self.weight_out)
        grad_bias_out = np.zeros_like(self.bias_out)
        for sample, advantage in zip(samples, advantages, strict=True):
            grad_mean = advantage * sample.noise / self.specification.exploration_std
            grad_weight_out += np.outer(sample.hidden_two, grad_mean)
            grad_bias_out += grad_mean
            grad_hidden_two = self.weight_out @ grad_mean
            grad_hidden_two *= 1.0 - sample.hidden_two**2
            grad_weight_two += np.outer(sample.hidden_one, grad_hidden_two)
            grad_bias_two += grad_hidden_two
            grad_hidden_one = self.weight_two @ grad_hidden_two
            grad_hidden_one *= 1.0 - sample.hidden_one**2
            grad_weight_one += np.outer(sample.features, grad_hidden_one)
            grad_bias_one += grad_hidden_one

        learning_rate = self.specification.learning_rate / len(samples)
        self.weight_one += learning_rate * np.clip(grad_weight_one, -10.0, 10.0)
        self.bias_one += learning_rate * np.clip(grad_bias_one, -10.0, 10.0)
        self.weight_two += learning_rate * np.clip(grad_weight_two, -10.0, 10.0)
        self.bias_two += learning_rate * np.clip(grad_bias_two, -10.0, 10.0)
        self.weight_out += learning_rate * np.clip(grad_weight_out, -10.0, 10.0)
        self.bias_out += learning_rate * np.clip(grad_bias_out, -10.0, 10.0)
        return float(returns[0])

    def save(self, path: Path) -> str:
        """Persist a model without pickle and return the reproducibility digest."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            specification=np.array(json.dumps(self.specification.to_dict(), sort_keys=True)),
            weight_one=self.weight_one,
            bias_one=self.bias_one,
            weight_two=self.weight_two,
            bias_two=self.bias_two,
            weight_out=self.weight_out,
            bias_out=self.bias_out,
        )
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @classmethod
    def load(cls, path: Path) -> StateMlpPolicy:
        """Load a persisted P06 model while rejecting pickle payloads."""
        with np.load(path, allow_pickle=False) as payload:
            raw_specification = json.loads(str(payload["specification"].item()))
            if not isinstance(raw_specification, dict):
                raise ValueError("Saved policy has an invalid architecture record")
            hidden_values = tuple(int(item) for item in raw_specification["hidden_layers"])
            if len(hidden_values) != 2:
                raise ValueError("Saved policy must specify exactly two hidden layers")
            specification = PolicySpecification(
                observation_size=int(raw_specification["observation_size"]),
                action_size=int(raw_specification["action_size"]),
                hidden_layers=(hidden_values[0], hidden_values[1]),
                exploration_std=float(raw_specification["exploration_std"]),
                learning_rate=float(raw_specification["learning_rate"]),
            )
            policy = cls(seed=0, specification=specification)
            policy.weight_one = np.asarray(payload["weight_one"], dtype=np.float64)
            policy.bias_one = np.asarray(payload["bias_one"], dtype=np.float64)
            policy.weight_two = np.asarray(payload["weight_two"], dtype=np.float64)
            policy.bias_two = np.asarray(payload["bias_two"], dtype=np.float64)
            policy.weight_out = np.asarray(payload["weight_out"], dtype=np.float64)
            policy.bias_out = np.asarray(payload["bias_out"], dtype=np.float64)
        return policy

    def _forward(
        self, observation: FloatMatrix
    ) -> tuple[FloatMatrix, FloatMatrix, FloatMatrix, FloatMatrix]:
        values = np.asarray(observation, dtype=np.float64)
        if values.shape != (self.specification.observation_size,):
            raise ValueError(f"Expected observation shape ({self.specification.observation_size},)")
        features = values / _OBSERVATION_SCALE
        hidden_one = np.tanh(features @ self.weight_one + self.bias_one)
        hidden_two = np.tanh(hidden_one @ self.weight_two + self.bias_two)
        mean = hidden_two @ self.weight_out + self.bias_out
        return features, hidden_one, hidden_two, mean
