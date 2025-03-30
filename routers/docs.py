from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter(
    tags=["Documentation"],
)

@router.get("/",
    summary="API Documentation",
    response_class=HTMLResponse)
async def root():
    """
    Custom HTML documentation for the API (default landing page).
    """
    html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GeeksForGeeks Analytics API Documentation</title>
            <style>
                :root {
                    --primary-color: #e4e4e4;
                    --secondary-color: #64ffda;
                    --background-color: #0a192f;
                    --code-background: #112240;
                    --text-color: #8892b0;
                    --heading-color: #ccd6f6;
                    --card-background: #112240;
                    --hover-color: #233554;
                    --gfg-green: #2f8d46;
                }
                body {
                    font-family: 'SF Mono', 'Fira Code', 'Monaco', monospace;
                    line-height: 1.6;
                    color: var(--text-color);
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 4rem 2rem;
                    background: var(--background-color);
                    transition: all 0.25s ease-in-out;
                }
                h1, h2, h3 {
                    color: var(--heading-color);
                    padding-bottom: 0.75rem;
                    margin-top: 2rem;
                    font-weight: 600;
                    letter-spacing: -0.5px;
                }
                h1 {
                    font-size: clamp(1.8rem, 4vw, 2.5rem);
                    margin-bottom: 2rem;
                    border-bottom: 2px solid var(--gfg-green);
                }
                .endpoint {
                    background: var(--card-background);
                    border-radius: 12px;
                    padding: 0;
                    margin: 1.5rem 0;
                    box-shadow: 0 10px 30px -15px rgba(2,12,27,0.7);
                    border: 1px solid var(--hover-color);
                    transition: all 0.2s ease-in-out;
                    overflow: hidden;
                }
                .endpoint-header {
                    padding: 1.5rem;
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    transition: background-color 0.2s ease;
                }
                .endpoint-header:hover {
                    background-color: var(--hover-color);
                }
                .endpoint-header h2 {
                    margin: 0;
                    padding: 0;
                    border: none;
                }
                .endpoint-content {
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.3s ease;
                    padding: 0 1.5rem;
                }
                .endpoint.active .endpoint-content {
                    max-height: 5000px; /* Large enough to show all content */
                    padding: 0 1.5rem 1.5rem;
                }
                .endpoint-toggle {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: var(--secondary-color);
                    transition: transform 0.3s ease;
                }
                .endpoint.active .endpoint-toggle {
                    transform: rotate(45deg);
                }
                code {
                    background: var(--code-background);
                    color: var(--secondary-color);
                    padding: 0.3rem 0.6rem;
                    border-radius: 6px;
                    font-family: 'SF Mono', 'Fira Code', monospace;
                    font-size: 0.85em;
                    word-break: break-word;
                    white-space: pre-wrap;
                }
                pre {
                    background: var(--code-background);
                    padding: 1.5rem;
                    border-radius: 12px;
                    overflow-x: auto;
                    margin: 1.5rem 0;
                    border: 1px solid var(--hover-color);
                    position: relative;
                }
                pre code {
                    padding: 0;
                    background: none;
                    color: var(--primary-color);
                    font-size: 0.9em;
                }
                .parameter {
                    margin: 1.5rem 0;
                    padding: 1.25rem;
                    border-left: 4px solid var(--gfg-green);
                    background: var(--hover-color);
                    border-radius: 0 8px 8px 0;
                    box-shadow: 0 4px 12px -6px rgba(2,12,27,0.4);
                    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
                }
                .parameter:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px -6px rgba(2,12,27,0.5);
                }
                .parameter code {
                    font-size: 0.95em;
                    font-weight: 500;
                    margin-right: 0.5rem;
                }
                .error-response {
                    border-left: 4px solid #ff79c6;
                    padding: 1.25rem;
                    margin: 1.25rem 0;
                    background: var(--hover-color);
                    border-radius: 0 8px 8px 0;
                    overflow-x: auto;
                }
                .note {
                    background: var(--hover-color);
                    border-left: 4px solid var(--gfg-green);
                    padding: 1.25rem;
                    margin: 1.25rem 0;
                    border-radius: 0 8px 8px 0;
                }
                footer {
                    margin-top: 3rem;
                    padding-top: 1.5rem;
                    border-top: 1px solid var(--hover-color);
                    text-align: center;
                    color: var(--text-color);
                    font-size: 0.9em;
                }
                p {
                    margin: 1.25rem 0;
                    font-size: 1rem;
                    line-height: 1.7;
                }
                @media (max-width: 768px) {
                    body {
                        padding: 1rem 0.75rem;
                    }
                    .endpoint-header {
                        padding: 1.25rem;
                    }
                    pre {
                        padding: 1rem;
                        font-size: 0.9em;
                    }
                    code {
                        font-size: 0.8em;
                    }
                }
                @media (max-width: 480px) {
                    body {
                        padding: 1rem 0.5rem;
                    }
                    .endpoint-header {
                        padding: 1rem;
                    }
                    h1 {
                        font-size: 1.8rem;
                    }
                    pre {
                        padding: 0.75rem;
                        font-size: 0.85em;
                    }
                    .parameter, .error-response, .note {
                        padding: 1rem;
                        margin: 1rem 0;
                    }
                }
                .method {
                    color: #ff79c6;
                    font-weight: bold;
                }
                .path {
                    color: var(--secondary-color);
                }
                .parameter {
                    margin: 1rem 0 1rem 1.5rem;
                    padding: 1rem;
                    border-left: 3px solid var(--gfg-green);
                    background: var(--hover-color);
                    border-radius: 0 8px 8px 0;
                }
                .error-section {
                    margin: 2rem 0;
                }
                .error-section h2 {
                    border-bottom: 2px solid var(--gfg-green);
                    padding-bottom: 0.75rem;
                }
                .error-toggle {
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem;
                    background: var(--card-background);
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    border: 1px solid var(--hover-color);
                }
                .error-toggle:hover {
                    background: var(--hover-color);
                }
                .error-toggle h3 {
                    margin: 0;
                    padding: 0;
                    border: none;
                }
                .error-content {
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.3s ease;
                }
                .error-item.active .error-content {
                    max-height: 1000px;
                }
                .error-toggle-icon {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: var(--secondary-color);
                    transition: transform 0.3s ease;
                }
                .error-item.active .error-toggle-icon {
                    transform: rotate(45deg);
                }
                ::selection {
                    background: var(--secondary-color);
                    color: var(--background-color);
                }
                .endpoint-method {
                    display: inline-block;
                    padding: 0.3rem 0.5rem;
                    background: var(--gfg-green);
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-right: 0.5rem;
                }
                .try-button {
                    display: inline-block;
                    margin-top: 1rem;
                    padding: 0.75rem 1.5rem;
                    background-color: var(--gfg-green);
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    text-decoration: none;
                    transition: all 0.2s ease;
                    border: none;
                    cursor: pointer;
                }
                .try-button:hover {
                    background-color: #3aa654;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .swagger-link {
                    position: fixed;
                    top: 1rem;
                    right: 1rem;
                    padding: 0.5rem 1rem;
                    background-color: var(--hover-color);
                    color: var(--heading-color);
                    border-radius: 4px;
                    text-decoration: none;
                    font-weight: bold;
                    border: 1px solid var(--gfg-green);
                    transition: all 0.2s ease;
                }
                .swagger-link:hover {
                    background-color: var(--gfg-green);
                    color: white;
                }
            </style>
        </head>
        <body>
            <a href="/docs" class="swagger-link">Swagger UI</a>
            <h1>GeeksForGeeks Stats API Documentation</h1>
            
            <p>This API provides access to GeeksForGeeks user statistics and problem-solving data. Click on each endpoint to see details.</p>

            <div class="endpoint">
                <div class="endpoint-header">
                    <h2><span class="endpoint-method">GET</span> User Statistics</h2>
                    <span class="endpoint-toggle">+</span>
                </div>
                <div class="endpoint-content">
                    <p><code class="path">/<span>{username}</span></code></p>
                    
                    <h3>Parameters</h3>
                    <div class="parameter">
                        <code>username</code> (path parameter): GeeksForGeeks username
                    </div>

                    <h3>Response Format</h3>
                    <pre>
<code>
{
    "userName": "example_user",
    "totalProblemsSolved": 150,
    "School": 20,
    "Basic": 35,
    "Easy": 50,
    "Medium": 30,
    "Hard": 15
}
</code>
                    </pre>

                    <h3>Example</h3>
                    <pre><code>GET /khantashif</code></pre>
                    
                    <a href="/docs#/User%20Stats/get_stats_by_path__username__get" class="try-button" target="_blank">Try it in Swagger UI</a>
                </div>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <h2><span class="endpoint-method">GET</span> User Profile</h2>
                    <span class="endpoint-toggle">+</span>
                </div>
                <div class="endpoint-content">
                    <p><code class="path">/<span>{username}</span>/profile</code></p>
                    
                    <h3>Parameters</h3>
                    <div class="parameter">
                        <code>username</code> (path parameter): GeeksForGeeks username
                    </div>

                    <h3>Response Format</h3>
                    <pre>
<code>
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
</code>
                    </pre>

                    <h3>Example</h3>
                    <pre><code>GET /khantashif/profile</code></pre>
                    
                    <a href="/docs#/User%20Profile/get_user_profile__username__profile_get" class="try-button" target="_blank">Try it in Swagger UI</a>
                </div>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <h2><span class="endpoint-method">GET</span> Solved Problems</h2>
                    <span class="endpoint-toggle">+</span>
                </div>
                <div class="endpoint-content">
                    <p><code class="path">/<span>{username}</span>/solved-problems</code></p>
                    
                    <h3>Parameters</h3>
                    <div class="parameter">
                        <code>username</code> (path parameter): GeeksForGeeks username
                    </div>

                    <h3>Response Format</h3>
                    <pre>
<code>
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
</code>
                    </pre>

                    <h3>Example</h3>
                    <pre><code>GET /khantashif/solved-problems</code></pre>
                    
                    <a href="/docs#/Problem%20Analysis/get_solved_problems__username__solved_problems_get" class="try-button" target="_blank">Try it in Swagger UI</a>
                </div>
            </div>

            <div class="error-section">
                <h2>Error Responses</h2>
                
                <div class="error-item">
                    <div class="error-toggle">
                        <h3>User not found</h3>
                        <span class="error-toggle-icon">+</span>
                    </div>
                    <div class="error-content">
                        <pre>
<code>{
    "error": true,
    "message": "User 'username' not found on GeeksForGeeks",
    "status_code": 404,
    "endpoint": "stats"
}</code>
                        </pre>
                    </div>
                </div>

                <div class="error-item">
                    <div class="error-toggle">
                        <h3>Service unavailable</h3>
                        <span class="error-toggle-icon">+</span>
                    </div>
                    <div class="error-content">
                        <pre>
<code>
{
    "error": true,
    "message": "Failed to connect to GeeksForGeeks. The service might be down or your internet connection is unstable.",
    "status_code": 503,
    "endpoint": "stats"
}
</code>
                        </pre>
                    </div>
                </div>
                
                <div class="error-item">
                    <div class="error-toggle">
                        <h3>Request timeout</h3>
                        <span class="error-toggle-icon">+</span>
                    </div>
                    <div class="error-content">
                        <pre>
<code>
{
    "error": true,
    "message": "Request to GeeksForGeeks timed out. Please try again later.",
    "status_code": 504,
    "endpoint": "stats"
}
</code>
                        </pre>
                    </div>
                </div>
            </div>

            <div class="note">
                <h2>Usage Notes</h2>
                <p>Please use this API responsibly and consider GeeksForGeeks' terms of service when making requests.</p>
            </div>

            <footer>
                <p>This API is open source and available on <a href="https://github.com/tashifkhan/GFG-Stats-API" style="color: var(--gfg-green); text-decoration: none;">GitHub</a>.</p>
                <p>Try it live at <a href="https://gfg-stats.tashif.codes" style="color: var(--gfg-green); text-decoration: none;">gfg-stats.tashif.codes</a></p>
            </footer>

            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Handle endpoint toggles
                    const endpoints = document.querySelectorAll('.endpoint');
                    endpoints.forEach(endpoint => {
                        const header = endpoint.querySelector('.endpoint-header');
                        header.addEventListener('click', () => {
                            endpoint.classList.toggle('active');
                        });
                    });
                    
                    // Handle error toggles
                    const errorItems = document.querySelectorAll('.error-item');
                    errorItems.forEach(item => {
                        const toggle = item.querySelector('.error-toggle');
                        toggle.addEventListener('click', () => {
                            item.classList.toggle('active');
                        });
                    });
                    
                    // Make the first endpoint active by default for better UX
                    if (endpoints.length > 0) {
                        endpoints[0].classList.add('active');
                    }
                });
            </script>
        </body>
        </html>
    """
    return HTMLResponse(content=html)


@router.get("/api-docs",
    summary="API Documentation")
async def api_docs():
    """Redirect to the Swagger UI documentation page"""
    return RedirectResponse(url="/docs")
