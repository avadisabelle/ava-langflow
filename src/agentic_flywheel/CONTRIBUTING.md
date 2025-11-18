# Contributing to Agentic Flywheel

We welcome contributions to the Agentic Flywheel project! By participating, you agree to abide by our Code of Conduct.

## 🚀 Getting Started

1.  **Fork the Repository:** Start by forking the [Agentic Flywheel repository](https://github.com/jgwill/agentic-flywheel).
2.  **Clone Your Fork:** Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/your-username/agentic-flywheel.git
    cd agentic-flywheel
    ```
3.  **Create a Virtual Environment:** It's recommended to work within a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows, use `venv\Scripts\activate`
    ```
4.  **Install Dependencies:** Install the project in editable mode along with development dependencies:
    ```bash
    pip install -e .[dev]
    ```

## 📝 Coding Guidelines

We adhere to the following coding standards:

*   **Formatting:** We use [Black](https://github.com/psf/black) for code formatting. Please run `black .` before committing.
*   **Imports:** We use [isort](https://pycqa.github.io/isort/) for sorting imports. Please run `isort .` before committing.
*   **Type Hinting:** We encourage the use of type hints for better code clarity and maintainability.
*   **Linting:** We use [MyPy](http://mypy-lang.org/) for static type checking. Run `mypy .` to check for type errors.

## 🧪 Running Tests

Tests are crucial for maintaining code quality. You can run them using `pytest`:

```bash
pytest
```

## 💡 Submitting Changes

1.  **Create a New Branch:** Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    ```
2.  **Make Your Changes:** Implement your changes, ensuring they follow the coding guidelines and are covered by tests.
3.  **Run Tests and Linters:** Before committing, ensure all tests pass and linters report no issues:
    ```bash
    pytest
    black .
    isort .
    mypy .
    ```
4.  **Commit Your Changes:** Write clear and concise commit messages. Reference any relevant issues (e.g., `feat(#123): Add new feature`).
5.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-feature-name
    ```
6.  **Open a Pull Request:** Go to the [Agentic Flywheel repository](https://github.com/jgwill/agentic-flywheel) on GitHub and open a pull request from your forked branch to the `main` branch.

## 📄 Code of Conduct

We expect all contributors to adhere to our Code of Conduct. Please read it carefully.

Thank you for contributing to the Agentic Flywheel!