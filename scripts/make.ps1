[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('help', 'setup', 'lint', 'typecheck', 'test', 'smoke', 'build', 'pre-commit')]
    [string]$Target
)

function Invoke-Uv {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & uv @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

switch ($Target) {
    'help' { Write-Output 'Targets: setup lint typecheck test smoke build pre-commit' }
    'setup' { Invoke-Uv sync --all-groups }
    'lint' { Invoke-Uv run ruff check . }
    'typecheck' { Invoke-Uv run mypy src tests }
    'test' { Invoke-Uv run pytest }
    'smoke' { Invoke-Uv run ora doctor --offline --output reports/environment/smoke.json }
    'build' { Invoke-Uv build }
    'pre-commit' { Invoke-Uv run pre-commit run --all-files }
}
