# Claude Development Notes

## Project Vision
**Minimal Viable Tutor (7 Topics)** - A CLI-first, web-ready Python learning system with SQLite-based progress tracking.

### Core Philosophy
- CLI-first approach for developer audience
- SQLite for scalable progress tracking (CLI → Web ready)
- Pedagogical principles: spaced repetition, interleaving, Socratic method
- Content creation focus over complex algorithms

## Implementation Plan (4-Week Roadmap)

### ✅ Phase 1: CLI + SQLite Foundation (Week 1) - COMPLETED
**Goal:** Basic CLI with database-backed progress tracking

**Completed Tasks:**
1. **Database Layer**
   - ✅ SQLite schema design (`users`, `user_progress` tables)
   - ✅ `ProgressPersistence` class with full CRUD operations
   - ✅ Database initialization and migration support
   - ✅ JSON serialization for complex data (completed_levels, performance_scores)

2. **CLI Module**
   - ✅ `cli.py` with Click framework
   - ✅ Commands: `list`, `learn <topic>`, `status`, `reset`
   - ✅ Default "cli_user" for single-user CLI mode
   - ✅ Learning session flow (display all 4 content levels)

3. **CurriculumEngine Integration**
   - ✅ Updated to use SQLite backend instead of mock progress
   - ✅ New methods: `load_user_progress`, `save_user_progress`, `update_topic_progress`
   - ✅ User statistics and progress analytics

4. **Testing & Quality**
   - ✅ 25 tests passing (unit + integration)
   - ✅ New test suite for `ProgressPersistence`
   - ✅ Updated existing tests for SQLite integration
   - ✅ CLI integration testing

**Success Criteria:** ✅ `python-tutor learn variables` displays all 4 levels and saves to SQLite

### 📋 Phase 2: Rich Interactive Experience (Week 2)
**Goal:** Beautiful, engaging learning sessions

**Planned Tasks:**
1. **Rich CLI Integration**
   - Syntax-highlighted code examples with Pygments
   - Progress bars and completion indicators
   - Color-coded content levels (concept/simple/medium/complex)
   - Interactive prompts and user input handling

2. **Code Execution Engine**
   - Subprocess-based Python execution with timeout
   - Output capture and comparison
   - Basic sandboxing (restrict file system access)
   - Error handling and display

3. **Socratic Learning Flow**
   - "Predict the output" exercises between levels
   - Interactive hints system for challenges
   - Challenge validation with immediate feedback

### 📋 Phase 3: Content Creation (Week 3)
**Goal:** All 7 topics with proper dependencies

**Planned Topics (in learning order):**
1. ✅ **Variables** (already exists)
2. **Conditionals** (prereq: variables)
3. **Lists** (prereq: variables)  
4. **Loops** (prereq: conditionals, lists)
5. **Dictionaries** (prereq: lists)
6. **Functions** (prereq: all above)
7. **Error Handling** (prereq: functions)

**Tasks:**
- JSON template generator for efficient topic creation
- Content validation and quality review scripts
- Prerequisite chain verification
- Database schema updates for topic metadata

### 📋 Phase 4: Polish & Analytics (Week 4)
**Goal:** Production-ready with insights

**Planned Features:**
- Advanced progress tracking (time spent, performance analytics)
- Spaced repetition suggestions based on completion dates
- Multi-user support foundation for web transition
- Comprehensive CLI integration tests
- Performance optimization

## Technical Decisions

### Why SQLite Over JSON Files?
- **CLI-Ready:** Perfect for single-user CLI application
- **Web-Ready:** Handles concurrent users for future web app
- **Query Power:** Analytics and progress queries with SQL
- **Migration Path:** Easy export to PostgreSQL when scaling beyond ~1000 users

### Why CLI Before Web?
- **Target Audience:** Python learners are typically developers (CLI comfort is valuable)
- **Development Speed:** Much faster iteration and validation
- **Architecture Validation:** Proves business logic before adding UI complexity
- **Strategic Path:** CLI → Web → Mobile as shown in README architecture

### Topic Sequence Rationale
Functions moved to 6th position (after dictionaries) because:
- Students need comfort with basic syntax before abstraction
- Functions can demonstrate examples using all previous concepts
- Creates natural "capstone" that ties everything together

### Dependency Management with pip-tools
**Why pip-tools over pyproject.toml dependencies:**
- **Reproducible Builds:** Locks exact versions with `pip-compile`
- **Clean Separation:** `.in` files for high-level deps, `.txt` files for lockfile
- **Easy Updates:** `pip-compile --upgrade` to update dependencies
- **No Conflicts:** Avoids mixing pyproject.toml and requirements approaches

**Workflow:**
```bash
# Install pip-tools
pip install pip-tools

# Update requirements
pip-compile requirements/base.in    # Generate base.txt
pip-compile requirements/dev.in     # Generate dev.txt

# Install dependencies
pip-sync requirements/dev.txt       # Sync to exact versions
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Business Logic │    │   Data Layer    │
│   (cli.py)      │◄──►│ (CurriculumEngine) │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Content Layer │
                       │  (JSON Topics)  │
                       └─────────────────┘
```

**Key Components:**
- **CLI Layer:** User interface with Click framework
- **CurriculumEngine:** Core learning logic and session management  
- **ProgressPersistence:** SQLite database operations
- **ContentLoader:** JSON topic file management
- **Models:** Data classes for type safety and validation

## Database Schema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    learning_path TEXT,
    global_stats TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_progress (
    user_id TEXT,
    topic_id TEXT,
    current_level INTEGER DEFAULT 0,
    completed_levels TEXT,      -- JSON array [0,1,2,3]
    performance_scores TEXT,    -- JSON array [0.8,0.9,0.7]
    last_accessed TIMESTAMP,
    total_time_spent INTEGER DEFAULT 0,
    challenge_attempts TEXT,    -- JSON object
    PRIMARY KEY (user_id, topic_id)
);
```

## Current CLI Usage

```bash
# Set up environment
export PYTHONPATH=src

# List available topics
python3 -m python_ai_tutor.cli list

# Start learning session
python3 -m python_ai_tutor.cli learn variables

# Check progress
python3 -m python_ai_tutor.cli status

# Reset progress
python3 -m python_ai_tutor.cli reset
```

## Testing Strategy
**Balanced Approach:** Implementation-first, then tests for stability
- **Database Layer:** Well tested (data integrity critical)
- **Core Logic:** Comprehensive unit tests
- **CLI Integration:** Basic happy path tests
- **Manual Testing:** During development for user experience

**Current Status:** 25 tests passing (updated for pip-tools setup)
- 7 ProgressPersistence tests
- 15 CurriculumEngine tests (including 3 new SQLite integration tests)
- 3 Integration tests
- Dependencies managed with pip-tools (no pre-commit hooks)

## Development Log

### Phase 1 Completion (Week 1)
**Achievements:**
- ✅ Complete SQLite backend implementation
- ✅ Functional CLI with all core commands
- ✅ Progress persistence working correctly
- ✅ All tests passing (25/25)
- ✅ Architecture proven with real variables topic

**Key Insights:**
- SQLite integration was straightforward and provides excellent foundation
- Click framework makes CLI development very clean
- Test-driven approach caught several edge cases early
- Variables topic JSON structure works well for all content types

**Challenges Overcome:**
- Python path configuration for CLI execution
- JSON serialization for complex progress data
- Database initialization timing in tests
- CLI user input handling for non-interactive execution

**Next Priority:** Rich formatting and code execution for engaging user experience

## Files Added/Modified

### New Files:
- `src/python_ai_tutor/progress_persistence.py` - SQLite backend
- `src/python_ai_tutor/cli.py` - Command line interface
- `tests/unit/test_progress_persistence.py` - Database tests
- `CLAUDE.md` - This documentation

### Modified Files:
- `src/python_ai_tutor/curriculum_engine.py` - Added SQLite integration
- `tests/unit/test_curriculum_engine.py` - Updated for SQLite backend
- `src/python_ai_tutor/models.py` - Added TopicProgress import (minor)

### Database Created:
- `user_data/progress.db` - SQLite database for progress tracking