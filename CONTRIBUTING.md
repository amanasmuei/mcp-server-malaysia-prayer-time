# Contributing to Malaysia Prayer Time MCP Server

Thank you for considering contributing to the Malaysia Prayer Time MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct, which is to be respectful and considerate of others.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers understand your report, reproduce the behavior, and find related reports.

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets which you use in those examples, as Markdown code blocks.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful** to most users.

### Pull Requests

* Fill in the required template
* Follow the style guidelines
* Document new code based on the project's documentation style
* Include tests that verify your changes
* End all files with a newline

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### TypeScript Styleguide

* Use 2 spaces for indentation
* Prefer `const` over `let`. Never use `var`
* Limit line length to 100 characters
* Place imports in the following order:
  * External packages (like `@modelcontextprotocol/sdk`)
  * Internal packages
  * Modules from parent directories
  * Modules from the same directory or child directories
* Place class properties in the following order:
  * Static properties and methods
  * Instance properties
  * Constructor
  * Instance methods

### Documentation Styleguide

* Use [Markdown](https://guides.github.com/features/mastering-markdown/) for documentation.
* Reference functions, classes, and modules in Markdown using backticks: \`Foo\`
* Document all public methods and properties using JSDoc style comments.

## Additional Notes

### Issue and Pull Request Labels

This section lists the labels we use to help us track and manage issues and pull requests.

* **bug** - Issues that are bugs
* **documentation** - Issues or PRs related to documentation
* **enhancement** - Issues that are feature requests or PRs that add functionality
* **good first issue** - Good for newcomers 