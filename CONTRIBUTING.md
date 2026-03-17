# Contributing to LinkedApiDoc

Thank you for contributing to LinkedApiDoc! This guide explains how to contribute changes, manage versions, and maintain the project.

## Version Management

### Incrementing the Version

LinkedApiDoc follows [Semantic Versioning (SemVer)](https://semver.org/):

- **MAJOR** version for incompatible changes
- **MINOR** version for backwards-compatible features
- **PATCH** version for backwards-compatible bug fixes

Update the version in `package.json`:

```json
{
  "version": "1.1.0"
}
```

### Documenting Changes

All changes must be documented in `VERSIONS.md`:

1. Add a new section with the version number and date
2. Categorize changes under:
   - `### Added` - new features
   - `### Changed` - changes in existing functionality
   - `### Deprecated` - soon-to-be removed features
   - `### Removed` - removed features
   - `### Fixed` - bug fixes
   - `### Security` - security improvements

Example:

```markdown
## [1.1.0] - 2026-03-17
### Added
- Filtrage automatique (sans "ApplyFilter").
- Recherche instantanée dans le champ "Route".
```

### Creating Git Tags

After making changes and updating the version:

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: automatic filtering and version management"

# Create an annotated tag
git tag -a v1.1.0 -m "Filtrage automatique et gestion des versions"

# Push the tag to remote
git push origin v1.1.0
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Modify the code as needed
- Test your changes locally
- Ensure existing functionality is not broken

### 3. Update Documentation

- Update `VERSIONS.md` with your changes
- Update `README.md` if new features are added

### 4. Commit and Push

```bash
git add .
git commit -m "feat: description of your change"
git push origin feature/your-feature-name
```

### 5. Create a Pull Request

Submit a pull request to the `main` branch for review.

## Code Style

- Use JavaScript vanilla (no external libraries for frontend)
- Follow existing code patterns
- Add comments for complex logic
- Use meaningful variable and function names

## Testing

Before submitting changes:

1. Test the application locally
2. Verify all existing features still work
3. Test new features thoroughly

## Questions?

Feel free to open an issue for any questions or suggestions.
