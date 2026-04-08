# Code Style

Author: Helmut Hoffer von Ankershoffen (@helmut-hoffer-von-ankershoffen ) - Status: Draft - Created: 2025-03-16 - Updated: 2025-03-16

This document describes the code style used in
[foundry-python](https://github.com/aignostics/foundry-python)
and derivatives. It defines strict requirements to be followed by all
contributors - humans and agents - to ensure consistency and readability across
the codebase.

## Code

We favor readability and maintainability over cleverness and brevity.

1. We always write code that is easy to read, understand, maintain, test,
  document, deploy, use, integrate, and extend.
2. We always write code that is efficient and performant, but only if it does not
  sacrifice readability, maintainability, and testability.
3. We always write code that is secure and does not introduce vulnerabilities.
4. We always write code that is portable and does not introduce platform-specific
  dependencies.
5. We always write code that is compatible with the Python version indicated in
  the .python-version file in the root of this repository.

## Naming

We believe that good names are essential for code readability and
maintainability. A good name is one that is descriptive, unambiguous, and
meaningful. It should convey the purpose and intent of the code it represents.

1. We take extra care to find proper names for all identifiers, including
  variables, functions, classes, types, tests, modules, and packages. We prefer
  descriptive names that clearly indicate the purpose and functionality of the
  code.
2. We avoid using abbreviations, acronyms, and jargon unless they are widely
  understood and accepted in the context of the code. We prefer full words and
  phrases that are easy to understand.
3. We avoid using single-letter names, except for loop variables and iterators.
4. We avoid using generic names like `data`, `info`, `temp`, `foo`, `bar`, etc.
  These names do not convey any meaning and make the code harder to read and
  understand.
5. We avoid using names that are too long or too short. A good name should be
  concise but descriptive. It should be long enough to convey the purpose and
  intent of the code, but not so long that it becomes cumbersome to read and
  write.
6. We avoid using names that are too similar or too different. A good name should
  be unique and distinct. It should not be confused with other names in the
  code. It should not be so different that it becomes hard to remember and
  recognize.

## Formatting

We use [ruff](https://github.com/astral-sh/ruff) to format Python code

1. The ruff formatter adheres to the
  [Black](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
  code style which is [PEP 8](https://www.python.org/dev/peps/pep-0008/)
  compliant.
2. The ruff formatter is configured to use a max line length of 120.
3. The ruff formatter is called by the lint session of nox.

Beyond PEP 8 we adhere to the following naming conventions: We use the following
conventions for Python code:

1. Class names: `PascalCase` - descriptive nouns that clearly indicate purpose.
2. Function/method names: `snake_case` - verb phrases that describe actions.
3. Variables/attributes: `snake_case` - descriptive nouns/noun phrases.
4. Constants: `UPPER_SNAKE_CASE`.
5. Private members: Prefix with single underscore `_private_attribute`.
6. "True" private members: Prefix with double underscore `__truly_private`.
7. Type variables: `CamelCase` with short, descriptive names (e.g., `T`, `KT`,
  `VT`).
8. Boolean variables/functions: Prefix with `is_`, `has_`, `should_`, etc.
9. Interface classes: Suffix with `Interface` or `Protocol`.

## Linting and type checking

We use [ruff](https://github.com/astral-sh/ruff) to lint Python code

1. All linting rules are enabled except those explicitly disabled in
  pyproject.toml
2. The ruff linter is called by the lint session of nox.

## Documentation

We use docstrings to document the purpose of modules, classes, types, functions,
its parameters and returns

1. We use Google style docstrings with typed Args and Returns.
2. We comment complex code and algorithms to explain their purpose and
  functionality.
3. We leave references with deep links in code to external documentation,
  standards, and specifications.

We provide an auto-generated OpenAPI specification and reference documentation.

1. Generation of documentation is called by the docs session of nox

## Testing

We use [pytest](https://docs.pytest.org/en/stable/) for testing Python code.

1. Tests are defined in the `tests/` directory
2. We use pytest fixtures to set up test data and state
3. We leverage several pytest plugins:
  1. `pytest-asyncio` for testing async code
  2. `pytest-cov` for coverage reporting
  3. `pytest-docker` for integration tests with containers
  4. `pytest-env` for environment variable management
  5. `pytest-regressions` for regression testing
  6. `pytest-xdist` for parallel test execution
4. Test execution is automated through the nox test session which runs across the
  Python versions indicated in the `pyproject.toml`.

Our test coverage is measured using `pytest-cov` and reported in the CI
pipeline.

1. We aim for 100% unit coverage on all code paths, including error handling and
  edge cases.
2. We fail the CI if unit test coverage drops below 85%.

Apart from unit tests we provide integration tests and end-to-end tests:

1. We smoke test as part of the CI/CD pipeline.
2. We facilitate exploratory testing to ensure comprehensive coverage.
3. We use `pytest-docker` for integration tests with containers.

## Error Handling

We use structured, explicit error handling that enables effective debugging and
monitoring:

1. Use specific exception classes instead of generic ones.
2. Include contextual information in exception messages.
3. Log exceptions with appropriate severity levels and context.
4. Gracefully degrade functionality when possible rather than failing completely.
5. Use type hints to catch type errors at compile time rather than runtime.
6. Design errors to be actionable for both users and developers.

## Logging

We log information to help with debugging and monitoring:

1. Use structured logging with consistent fields across all log entries.
2. Include correlation IDs for tracking requests across components.
3. Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
4. Be mindful of PII and sensitive data in logs, using obfuscation where needed.
5. Consider log volume and performance impact in production environments.

## Performance Considerations

We consider performance from the early design stage, not as an afterthought:

1. Consider algorithmic complexity (Big O notation) for all operations.
2. Prefer lazy evaluation when dealing with large datasets.
3. Use appropriate data structures for specific access patterns.
4. Be mindful of memory usage, especially for long-running processes.
5. Consider profiling for critical paths and potential bottlenecks.
6. Document performance characteristics and assumptions.
7. Write benchmarks for performance-critical code.
8. Design for horizontal scaling from the beginning.
9. Use asynchronous operations appropriately for I/O-bound tasks.
10. Consider caching strategies when appropriate.

## API Design

For both internal and external APIs we follow the principle of least surprise.

1. We maintain backward compatibility whenever possible. If not possible we add a
  new major version of the API.
2. Implement proper versioning for breaking changes.
3. Document error conditions, return values, and side effects.
4. Design for testability and mockability.
5. Provide sensible defaults while allowing for configuration.
6. Follow RESTful principles for HTTP APIs.
7. Use consistent parameter ordering and naming.
8. Implement proper validation with helpful error messages.
9. Consider rate limiting and circuit breaking for external services.

## Security

We prioritize security at every stage of development to prevent vulnerabilities
and protect our users.

1. Follow the principle of least privilege for all operations and access
  controls.
2. Never store secrets (API keys, passwords, tokens) in code repositories.
  1. Use environment variables or dedicated secret management services.
  2. Code is checked via `detect-secrets` pre-commit hook to prevent accidental
    commits of secrets.

We implement proper input validation and sanitization for all external inputs
via [pydantic](https://pydantic-docs.helpmanual.io/):

1. Validate inputs as early as possible in the data flow.

We handle authentication and authorization correctly:

1. Use industry-standard authentication protocols (OAuth, JWT).
2. Separate authentication from authorization logic.
3. Implement proper session management with secure cookies.
4. Protect against common vulnerabilities:
  1. SQL Injection: Use parameterized queries or ORM frameworks.
  2. XSS: Apply proper output encoding.
  3. CSRF: Implement anti-CSRF tokens for state-changing operations.
  4. SSRF: Validate and restrict URL destinations.
  5. Command Injection: Avoid direct system command execution where possible.
5. Implement proper error handling that doesn't leak sensitive information.
6. Use secure defaults and fail closed (secure) rather than open (insecure).

We apply the principle of defense in depth:

1. Don't rely on a single security control.
2. Implement multiple layers of protection.
3. Document security considerations in code and design documents.
4. Write security-focused tests:
  1. Test for security property violations.
  2. Test error cases and edge conditions.
  3. Test for resource exhaustion scenarios.
5. Apply proper rate limiting and throttling to prevent abuse.
6. For cryptographic operations:
  1. Use established libraries, not custom implementations.
  2. Follow current best practices for algorithm selection and key management.
  3. Be aware of the limitations of cryptographic primitives.
7. Regularly run security-focused static analysis tools as part of CI/CD:
  1. SonarCloud checks for security vulnerabilities

Our security posture is defined in [SECURITY.md](SECURITY.md).

## Dependency Management

We use modern dependency management practices:

1. [uv](https://github.com/astral-sh/uv) for fast, reliable package installation
  and environment management
2. Dependency version locking via uv.lock file
3. Regular dependency auditing:
  1. Security auditing via `pip-audit`
  2. License compliance checks via `pip-licenses`
  3. SBOM generation via `cyclonedx-py`

Dependency updates are automated using two complementary tools:

- **[Renovate](https://github.com/renovatebot/renovate)**: Handles version updates for direct
  dependencies (Python packages, GitHub Actions) with grouped PRs and weekly lock file maintenance
  to keep transitive dependencies fresh
- **[Dependabot](https://docs.github.com/en/code-security/dependabot)**: Handles security alerts
  and creates targeted PRs for vulnerable transitive dependencies

## Versioning

We use [semantic versioning](https://semver.org/) for versioning our releases:

1. MAJOR: Breaking changes
2. MINOR: New features, non-breaking changes
3. PATCH: Bug fixes, non-breaking changes

Our API versioning follows the same principles, with major versions indicated in
the URL (e.g., /api/v1/resource) and the full version provided as part of the
OpenAPI pecification.

## Conventional Commits

Our commit messages follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) definition.

1. We use `feat`, `fix`, `chore`, `docs`, `style`, `perf`, `refactor`, `test` prefixes and
  components in parentheses. E.g.
  `feat(api): add new endpoint for user registration`.

## PR Title Conventions

PR titles must follow the same conventional commits format as commit messages. This is
enforced because squash merges use the PR title as the commit message.

Format: `<type>(<scope>): <description>`

Examples:

- `feat(api): add user authentication endpoint`
- `fix(parser): handle empty input gracefully`
- `docs: update installation guide`

## Guidance for AI Pair Programming

When generating code with AI assistance:

1. AI-generated code must follow all style guidelines in this document.
2. Always review AI-generated code for correctness, security implications, and
  adherence to project patterns.
3. Use AI to generate tests alongside implementation code.
4. Request explanations for complex algorithms or patterns in the generated code.
5. Remember that AI should augment, not replace, human judgment about code
  quality and design decisions.
