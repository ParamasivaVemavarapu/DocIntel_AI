# Engineering Quality

DocIntel AI is structured as a full-stack software product rather than a notebook-only AI demonstration.

## Quality Controls

- **Modular backend:** API routes, configuration, schemas, and domain logic are separated into reusable Python modules.
- **Typed interfaces:** FastAPI response models and TypeScript frontend types define service contracts.
- **Configuration:** runtime values are loaded from environment variables through Pydantic Settings; secrets are excluded from source control.
- **Error handling:** invalid files, unsupported formats, missing records, and malformed inputs return explicit HTTP errors.
- **Testing:** backend unit tests run with coverage reporting on every push and pull request.
- **Static checks:** Ruff linting, Python import compilation, and TypeScript type checking run in CI.
- **Reproducible builds:** locked npm dependencies, pinned Python dependencies, Dockerfiles, and Docker Compose support consistent environments.
- **Container verification:** CI validates the Compose model and builds all application images.
- **Documentation:** the README covers the product, architecture, API, configuration, limitations, and local operation.

## CI Pipeline

1. Install pinned backend and developer dependencies.
2. Lint Python and compile backend modules.
3. Run pytest with a visible coverage report and minimum coverage gate.
4. Install frontend packages with `npm ci`.
5. Type-check and create a production Next.js build.
6. Validate Docker Compose and build the container images.

## Production Readiness Boundary

The repository demonstrates deployable application packaging, but it does not claim a live cloud deployment. Production rollout would additionally require managed secrets, HTTPS, centralized logs and metrics, identity/RBAC, persistent managed storage, vulnerability scanning, backups, and environment-specific infrastructure.

## Evaluation

Current outputs demonstrate the implemented workflow. Model or retrieval metrics are reported only when backed by a labeled evaluation dataset and a reproducible evaluation script. Roadmap metrics are not presented as achieved results.
