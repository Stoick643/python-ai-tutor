# Python AI Tutor

An intelligent, adaptive Python learning system with CLI interface that guides users through personalized Python education using proven pedagogical principles.

## Features

- **4-Level Learning Structure**: Concept → Simple → Medium → Complex examples
- **Adaptive Difficulty**: Real-time content adjustment based on performance
- **Interactive Code Execution**: Run and test code directly in the tutor
- **Progress Tracking**: Local JSON-based progress persistence
- **Smart Scheduling**: Prerequisite-based topic ordering with spaced repetition
- **Socratic Teaching**: AI-powered on-demand lectures that guide discovery
- **Multiple Learning Paths**: Specialized tracks for web dev, data analysis, automation

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/python-ai-tutor.git
cd python-ai-tutor

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install pip-tools
pip-sync requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Start learning
python-tutor learn variables
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │  Business Logic │    │   Data Layer    │
│  (CLI/Web/App)  │◄──►│   (Tutor Core)  │◄──►│  (Persistence)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **Modular Design**: Separate UI/Logic/Data for future expansion (CLI → Web → Mobile)
- **TDD Approach**: Test-driven development for core business logic
- **Quality Assurance**: Pre-commit hooks with Black, Ruff, and MyPy

## Development Setup

### Dependencies
- Python 3.10+
- Virtual environment (venv)
- pip-tools for reproducible builds

### Development Tools
- **Testing**: pytest, pytest-cov, pytest-mock
- **Code Quality**: black, ruff, mypy, pre-commit
- **Documentation**: mkdocs, mkdocs-material

### Project Structure
```
python-ai-tutor/
├── src/python_ai_tutor/     # Main source code
├── tests/                   # Test files
├── curriculum/              # Learning content (JSON)
├── docs/                    # Documentation
├── requirements/            # Dependency management
└── user_data/              # Local progress storage
```

## Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Project setup with venv + pip-tools
- [x] Development environment (pytest, black, mypy, pre-commit)
- [ ] Core curriculum engine with JSON-based topics
- [ ] CLI interface with Rich formatting
- [ ] Local progress tracking

### Phase 2: Content & Intelligence (Weeks 3-4)
- [ ] 20 core Python topics with 4-level structure
- [ ] Adaptive difficulty system
- [ ] Prerequisite-based topic ordering
- [ ] Coding challenges with validation

### Phase 3: Enhancement (Weeks 5-6)
- [ ] Spaced repetition algorithms
- [ ] Personalized learning paths
- [ ] Progress analytics dashboard
- [ ] Quality assurance system

### Phase 4: AI Teaching Assistant (Week 7+)
- [ ] On-demand lecture generation
- [ ] Socratic teaching methods
- [ ] Conversational learning flow
- [ ] Understanding verification

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run pre-commit hooks (`pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with pedagogical principles from cognitive science research
- Inspired by proven educational techniques: spaced repetition, interleaving, Socratic method
- Uses modern Python development practices and tools
