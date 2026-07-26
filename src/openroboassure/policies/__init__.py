"""Comparable scripted and learned policy interfaces for P06."""

from openroboassure.policies.mlp import PolicySpecification, StateMlpPolicy
from openroboassure.policies.scripted import ScriptedPickPlacePolicy

__all__ = ["PolicySpecification", "ScriptedPickPlacePolicy", "StateMlpPolicy"]
