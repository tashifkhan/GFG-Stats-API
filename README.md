# GFG-Stats-API

A robust RESTful API to fetch and display GeeksForGeeks statistics for users, built with FastAPI.

Hosted at [gfg-stats.tashif.codes](https://gfg-stats.tashif.codes)

## Interactive Dashboard

The API now features a rich, interactive dashboard that you can use to explore GeeksForGeeks user profiles directly in your browser.

- **Live User Stats:** Enter any GFG username to get up-to-date statistics.
- **Visualized Data:** See problem-solving stats visualized in a clean, readable bar chart.
- **Detailed Profile:** View key profile information like coding score, institute rank, and streaks in a modern card-based layout.
- **Seamless API Documentation:** The dashboard is integrated with the API documentation, so you can explore the data and the API in one place.

## Features

- Retrieve user's solved problems count (school, basic, easy, medium, hard)
- Get detailed submission statistics (all the solved prolems and history)
- View coding scores and practice points
- Track performance over time
- Get any users profile data
- Easy integration with other applications
- Rate-limited endpoints to prevent abuse

## API Endpoints

### Get User Statistics

```
GET /{username}
```

Retrieves the basic statistics for a GeeksForGeeks user.

#### Parameters

- `username` (path): GeeksForGeeks username

#### Response

Returns user's GeeksForGeeks statistics including:

- Total solved problems (by difficulty)
- Solved problem counts by difficulty level (School, Basic, Easy, Medium, Hard)

#### Example Response

```json
{
	"userName": "example_user",
	"totalProblemsSolved": 150,
	"School": 20,
	"Basic": 35,
	"Easy": 50,
	"Medium": 30,
	"Hard": 15
}
```

### Get User Profile

```
GET /{username}/profile
```

Retrieves detailed profile information for a user.

#### Parameters

- `username` (path): GeeksForGeeks username

#### Response

Returns:

- Profile information
- Institution details
- Coding metrics
- Streak information

#### Example Response

```json
{
	"userName": "example_user",
	"fullName": "Example User",
	"profilePicture": "https://example.com/profile.jpg",
	"institute": "Example University",
	"instituteRank": "10",
	"currentStreak": "5",
	"maxStreak": "15",
	"codingScore": 1200,
	"monthlyScore": 250,
	"totalProblemsSolved": 150
}
```

### Get Solved Problems

```
GET /{username}/solved-problems
```

Retrieves detailed problem solving statistics for a user.

#### Parameters

- `username` (path): GeeksForGeeks username

#### Response

Returns:

- Total problems solved
- Problems solved by difficulty
- Detailed list of solved problems with links and difficulty levels

#### Example Response

```json
{
	"userName": "example_user",
	"totalProblemsSolved": 150,
	"problemsByDifficulty": {
		"school": 20,
		"basic": 35,
		"easy": 50,
		"medium": 30,
		"hard": 15
	},
	"problems": [
		{
			"question": "Two Sum",
			"questionUrl": "https://practice.geeksforgeeks.org/problems/two-sum",
			"difficulty": "easy"
		},
		{
			"question": "Merge Two Sorted Lists",
			"questionUrl": "https://practice.geeksforgeeks.org/problems/merge-two-sorted-lists",
			"difficulty": "medium"
		}
		// ... more problems
	]
}
```

## API Documentation

The API documentation is integrated with an interactive dashboard. Visit the root URL when the server is running:

```
GET /
```

For standard API documentation interfaces, you can use:

For Swagger UI documentation:

```
GET /docs
```

or

```
GET /api-docs
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Request successful
- `404 Not Found`: User not found
- `503 Service Unavailable`: Failed to connect to GeeksForGeeks
- `504 Gateway Timeout`: Request to GeeksForGeeks timed out

Error responses follow this format:

```json
{
	"error": true,
	"message": "error description",
	"status_code": 404,
	"endpoint": "stats"
}
```

## Usage Examples

### Python

```python
import requests

username = "gfgcoder"
response = requests.get(f"https://gfg-stats.tashif.codes/{username}")
data = response.json()

print(f"{username} has solved {data['totalProblemsSolved']} problems!")
```

### JavaScript

```javascript
fetch(`https://gfg-stats.tashif.codes/${username}`)
	.then((response) => response.json())
	.then((data) => console.log(data));
```

## Installation

### Setup

1. Clone the repository

   ```bash
   git clone https://github.com/tashifkhan/GFG-Stats-API.git
   cd GFG-Stats-API
   ```

2. Create a virtual environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

4. Start the server
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:58353`.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

Full API documentation is available at `/` endpoint when the server is running.

## License

MIT License. See [LICENSE](LICENSE) for more information.
