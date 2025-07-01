# Implementation Notes & Technical Decisions

## Docker Strategy

### Base Image Choice
**Decision**: Use `python:3.12-alpine3.19`
**Rationale**:
- Alpine Linux for minimal size (~5MB base vs ~100MB+ Ubuntu)
- Python 3.12 for latest features and security
- Official Python images are well-maintained
- Alpine has excellent package manager (apk)

### Multi-Stage Build Approach
**Decision**: Implement in Phase 2 (not Phase 1)
**Rationale**:
- Phase 1 focuses on working solution
- Multi-stage adds complexity but significant size benefits
- Easier to debug single-stage initially

## Security Considerations

### Non-Root User
**Implementation**:
```dockerfile
RUN addgroup -g 1000 ytdlp && \
    adduser -u 1000 -G ytdlp -s /bin/sh -D ytdlp
USER ytdlp
```
**Rationale**:
- Prevents privilege escalation attacks
- Standard practice for production containers
- UID/GID 1000 is conventional for first user

### Dependency Pinning
**Strategy**: Pin major.minor versions, allow patch updates
```txt
yt-dlp>=2024.12.13,<2025.0.0
requests>=2.31.0,<3.0.0
```
**Rationale**:
- Security updates via patch versions
- Prevent breaking changes from major updates
- Reproducible builds

## Performance Optimizations

### Layer Optimization
**Best Practices**:
1. Combine RUN commands to reduce layers
2. Install dependencies before copying application code
3. Use .dockerignore to exclude unnecessary files
4. Clean package manager cache in same RUN command

### Download Directory Strategy
**Decision**: Use `/downloads` as working directory
**Rationale**:
- Clear, intuitive path
- Easy to mount as volume
- Matches user expectations

## Configuration Management

### Environment Variables
**Key Variables**:
- `YTDL_FORMAT` - Video format preference
- `YTDL_OUTPUT_TEMPLATE` - Output filename template
- `YTDL_EXTRACT_FLAT` - Playlist handling
- `YTDL_WRITE_INFO_JSON` - Metadata files

**Implementation**:
```bash
# In entrypoint.sh
FORMAT=${YTDL_FORMAT:-"best[height<=720]"}
OUTPUT_TEMPLATE=${YTDL_OUTPUT_TEMPLATE:-"%(uploader)s/%(title)s.%(ext)s"}
```

### Config File Support
**Phase 2 Feature**: Mount config files
**Location**: `/home/ytdlp/.config/yt-dlp/config`

## Error Handling Strategy

### Entrypoint Script
**Approach**: Fail fast with clear error messages
```bash
set -e  # Exit on any error
set -u  # Exit on undefined variables
```

### Health Checks
**Strategy**: Lightweight version check
```bash
yt-dlp --version >/dev/null 2>&1
```

## Build Process

### Makefile Targets
**Essential Targets**:
- `build` - Standard build
- `build-dev` - Development build with debug tools
- `test` - Run automated tests
- `clean` - Remove images and containers
- `push` - Push to registry

### Version Management
**Strategy**: Semantic versioning in VERSION file
- Format: `MAJOR.MINOR.PATCH`
- Increment rules:
  - MAJOR: Breaking changes
  - MINOR: New features
  - PATCH: Bug fixes

## Testing Strategy

### Unit Tests
**Phase 1**: Basic functionality tests
- Container starts successfully
- yt-dlp version accessible
- Downloads directory writable

### Integration Tests  
**Phase 2**: Real download tests
- Download public domain video
- Verify output format
- Check metadata extraction

### Security Tests
**Phase 3**: Automated security scanning
- Trivy for vulnerability scanning
- Hadolint for Dockerfile linting
- Container structure tests

## CI/CD Pipeline Design

### Trigger Events
- Push to main branch
- Pull requests
- Weekly scheduled builds (dependency updates)
- Manual triggers

### Build Matrix
**Multi-Architecture Support**:
- linux/amd64 (Intel/AMD)
- linux/arm64 (Apple Silicon, ARM servers)

### Registry Strategy
**Phase 3**: Multi-registry publishing
- GitHub Container Registry (primary)
- Docker Hub (public access)
- Private registry option

## Monitoring & Observability

### Health Checks
**Docker Health Check**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh
```

### Logging Strategy
**Structured Logging**:
- JSON format for machine parsing
- Include timestamp, level, message
- Separate application vs system logs

## Future Considerations

### Web UI Integration
**Potential**: yt-dlp-web-ui integration
**Complexity**: Medium (requires additional services)

### Kubernetes Support
**Phase 4**: Helm charts and K8s manifests
**Use Case**: Large-scale deployments

### Plugin System
**Advanced**: Support for yt-dlp plugins
**Challenge**: Security implications of dynamic loading

## Development Workflow

### Local Development
1. Edit Dockerfile/scripts
2. `make build` - Build image
3. `make test` - Run tests
4. `docker run` - Manual testing
5. Commit changes

### Production Deployment
1. Tag release in git
2. CI/CD builds multi-arch images
3. Security scan passes
4. Auto-deploy to registry
5. Update documentation

## Common Pitfalls to Avoid

1. **Large Image Size**: Use multi-stage builds
2. **Security Issues**: Always use non-root user
3. **Dependency Hell**: Pin versions explicitly
4. **Poor Caching**: Order Dockerfile layers carefully
5. **No Health Checks**: Always implement health endpoints
6. **Hardcoded Values**: Use environment variables
7. **No Documentation**: Keep docs updated with code 