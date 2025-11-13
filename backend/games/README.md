# Games Module - Conversa

## Overview

The **Games Module** provides interactive language learning games for Conversa events. Games are collaborative activities where confirmed participants vote together on answers.

## Features

- **Game Types**: Picture Description, Word Association, Debate, Role Play
- **Difficulty Levels**: Easy, Medium, Hard
- **Collaborative Voting**: Participants vote together, majority decides
- **Auto-timeout**: Games automatically timeout after configured duration
- **Multilingual**: Content available in French, English, and Dutch

## Architecture

### Models

#### Game
- **Fields**:
  - `public_id`: UUID for external references
  - `event`: Foreign key to Event
  - `created_by`: Foreign key to User (organizer)
  - `game_type`: Choice field (picture_description, word_association, etc.)
  - `difficulty`: Choice field (easy, medium, hard)
  - `language_code`: Language of the game content
  - `question_text`: The question displayed to participants
  - `correct_answer`: The correct answer
  - `timeout_at`: Auto-timeout deadline
  - `status`: ACTIVE, COMPLETED, or TIMEOUT
  - `is_correct`: Whether team answered correctly
  - `final_answer`: The answer chosen by majority vote

#### GameVote
- **Fields**:
  - `game`: Foreign key to Game
  - `user`: Foreign key to User
  - `answer`: The vote answer
- **Constraints**: One vote per user per game

### Services

#### GameService

The service layer contains all business logic:

- `create_game()`: Create a new game for an event
  - Validates organizer permission
  - Validates event is active
  - Ensures no other active game exists
  - Randomly selects question from JSON files

- `submit_vote()`: Submit a participant's vote
  - Validates user is confirmed participant
  - Prevents duplicate votes
  - Checks if game should auto-complete

- `process_timeout()`: Handle game timeout
  - Called by scheduled task

- `get_game_stats()`: Get real-time voting statistics

### API Endpoints

All endpoints are under `/api/v1/games/`

#### List Games
```
GET /api/v1/games/
```
- Query params: `event_id`, `status`
- Returns: List of games for events user has access to

#### Get Game Details
```
GET /api/v1/games/{id}/
```
- Returns: Game details with votes and statistics

#### Create Game
```
POST /api/v1/games/create/
```
- Body:
  ```json
  {
    "event_id": 1,
    "game_type": "picture_description",
    "difficulty": "medium",
    "timeout_minutes": 5
  }
  ```
- Permissions: Event organizer only
- Returns: Created game

#### Submit Vote
```
POST /api/v1/games/{id}/vote/
```
- Body:
  ```json
  {
    "answer": "mountain"
  }
  ```
- Permissions: Confirmed participants only
- Returns: Updated game (may be completed)

#### Get Game Statistics
```
GET /api/v1/games/{id}/stats/
```
- Returns:
  ```json
  {
    "total_votes": 3,
    "confirmed_participants": 5,
    "vote_counts": {
      "mountain": 2,
      "beach": 1
    },
    "votes_remaining": 2,
    "time_remaining_seconds": 180
  }
  ```

#### Get Active Game
```
GET /api/v1/games/active/?event_id=1
```
- Returns: Currently active game for the event (if any)

## Business Rules

### Game Creation
1. Only event organizer can create games
2. Event must be PUBLISHED and currently active (started but not finished)
3. Only one active game per event at a time
4. Game content is randomly selected based on type and difficulty

### Voting
1. Only confirmed participants can vote
2. One vote per participant per game
3. Votes are immutable (cannot be changed)
4. Game completes when:
   - All participants have voted, OR
   - Majority (>50%) vote for the same answer

### Timeout
1. Games auto-timeout after configured duration (default 5 minutes)
2. Timed-out games have `status=TIMEOUT` and `is_correct=null`
3. Scheduled task runs periodically to process timeouts

## Game Content

Game content is stored in JSON files under `backend/fixtures/games/`:

### File Naming
```
{game_type}_{language_code}.json
```

Examples:
- `picture_description_fr.json`
- `word_association_en.json`

### JSON Structure
```json
[
  {
    "id": "pd_fr_easy_01",
    "difficulty": "easy",
    "question": "Décrivez cette image : Qu'est-ce que vous voyez ?",
    "image_url": "https://images.unsplash.com/photo-...",
    "correct_answer": "montagne",
    "options": ["montagne", "plage", "ville", "forêt"],
    "context": "Une belle montagne avec de la neige au sommet"
  }
]
```

### Available Content
- **Picture Description** (FR, EN, NL): 9 questions per language
- **Word Association** (FR, EN, NL): 9 questions per language

## Adding New Game Content

1. Create JSON file: `backend/fixtures/games/{game_type}_{lang}.json`
2. Follow the structure above
3. Add at least 3 questions per difficulty level
4. Restart server to clear cache

## Adding New Game Types

1. Add to `GameType` enum in `models.py`
2. Create JSON content files for each language
3. No code changes needed - service auto-loads content

## Testing

```bash
# Run tests
pytest backend/games/tests/

# Test game creation
curl -X POST http://localhost:8000/api/v1/games/create/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "game_type": "picture_description", "difficulty": "easy"}'

# Test voting
curl -X POST http://localhost:8000/api/v1/games/1/vote/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"answer": "mountain"}'
```

## Permissions

| Action | Permission |
|--------|-----------|
| Create game | Event organizer only |
| Vote | Confirmed participants only |
| View games | Participants of event or organizer |
| List games | Filter by accessible events |

## Database Schema

```sql
-- Game table
CREATE TABLE games_game (
    id BIGINT PRIMARY KEY,
    public_id UUID UNIQUE,
    event_id BIGINT REFERENCES events_event(id),
    created_by_id BIGINT REFERENCES users_user(id),
    game_type VARCHAR(32),
    difficulty VARCHAR(10),
    language_code VARCHAR(5),
    question_id VARCHAR(50),
    question_text TEXT,
    correct_answer VARCHAR(255),
    image_url VARCHAR(200),
    timeout_minutes INT,
    timeout_at TIMESTAMP,
    status VARCHAR(16),
    completed_at TIMESTAMP,
    is_correct BOOLEAN,
    final_answer VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- GameVote table
CREATE TABLE games_gamevote (
    id BIGINT PRIMARY KEY,
    game_id BIGINT REFERENCES games_game(id),
    user_id BIGINT REFERENCES users_user(id),
    answer VARCHAR(255),
    created_at TIMESTAMP,
    CONSTRAINT unique_vote_per_user_per_game UNIQUE (game_id, user_id)
);
```

## Scheduled Tasks

Add to your task scheduler (Celery, cron, etc.):

```python
from games.services import GameService

# Run every minute to process timeouts
def process_game_timeouts():
    count = GameService.check_timeouts()
    print(f"Processed {count} timed-out games")
```

## Frontend Integration

See `frontend/src/app/features/games/` for Angular components and services.

Key components:
- `GameListComponent`: Display available games
- `GamePlayComponent`: Active game interface with voting
- `GameResultsComponent`: Show completed game results

## Troubleshooting

### Game content not loading
- Check JSON files exist in `backend/fixtures/games/`
- Verify file naming: `{game_type}_{language_code}.json`
- Restart server to clear cache

### Votes not registering
- Ensure user has confirmed booking for the event
- Check game status is ACTIVE
- Verify user hasn't already voted

### Games not timing out
- Ensure scheduled task is running
- Check `GameService.check_timeouts()` is called periodically

## Future Enhancements

- [ ] Support for debate games with free-text responses
- [ ] Role-play scenarios with structured dialogues
- [ ] Team scoring and leaderboards
- [ ] Real-time WebSocket updates for live voting
- [ ] Audio/video content for advanced games
- [ ] Custom game creation by organizers
