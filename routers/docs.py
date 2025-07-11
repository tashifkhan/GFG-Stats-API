from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

docs_router = APIRouter()

docs_html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeeksForGeeks Analytics Dashboard and API Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
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
        }
        h1, h2, h3 {
            color: var(--heading-color);
            padding-bottom: 0.75rem;
            margin-top: 2rem;
            font-weight: 600;
        }
        h1 {
            font-size: clamp(1.8rem, 4vw, 2.5rem);
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--gfg-green);
        }
        .swagger-link {
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
        .stalker-form {
            background: var(--card-background);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid var(--hover-color);
            text-align: center;
        }
        .input-group {
            display: flex;
            gap: 1rem;
            max-width: 500px;
            margin: 0 auto;
        }
        .input-group input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 2px solid var(--hover-color);
            border-radius: 8px;
            background: var(--code-background);
            color: var(--text-color);
            font-family: inherit;
            font-size: 1rem;
        }
        .input-group input:focus {
            outline: none;
            border-color: var(--gfg-green);
        }
        .stalk-button {
            padding: 0.75rem 1.5rem;
            background: var(--gfg-green);
            color: white;
            border: none;
            border-radius: 8px;
            font-family: inherit;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        .input-container {
            position: relative;
            flex: 1;
            display: flex;
            align-items: center;
        }
        .clear-history-btn {
            position: absolute;
            right: 0.5rem;
            background: none;
            border: none;
            color: var(--text-color);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            opacity: 0.7;
        }
        .clear-history-btn:hover {
            opacity: 1;
            color: var(--secondary-color);
            background: var(--hover-color);
        }
        .clear-history-btn .icon {
            width: 1rem;
            height: 1rem;
        }
        .history-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--card-background);
            border: 1px solid var(--hover-color);
            border-top: none;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 8px 25px rgba(2,12,27,0.3);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-height: 300px;
            overflow: hidden;
        }
        .history-dropdown.active {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }
        .dropdown-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--hover-color);
            background: var(--hover-color);
        }
        .dropdown-header span {
            color: var(--heading-color);
            font-size: 0.9rem;
            font-weight: 600;
        }
        .clear-all-btn {
            background: none;
            border: none;
            color: var(--text-color);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            opacity: 0.7;
        }
        .clear-all-btn:hover {
            opacity: 1;
            color: var(--secondary-color);
            background: var(--card-background);
        }
        .clear-all-btn .icon {
            width: 1rem;
            height: 1rem;
        }
        .history-list {
            max-height: 250px;
            overflow-y: auto;
        }
        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
            border-bottom: 1px solid rgba(136, 146, 176, 0.1);
        }
        .history-item:last-child {
            border-bottom: none;
        }
        .history-item:hover {
            background: var(--hover-color);
        }
        .history-item.selected {
            background: var(--secondary-color);
            color: var(--background-color);
        }
        .history-username {
            color: var(--text-color);
            font-weight: 500;
            flex: 1;
        }
        .history-item:hover .history-username,
        .history-item.selected .history-username {
            color: inherit;
        }
        .history-delete-btn {
            background: none;
            border: none;
            color: var(--text-color);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            opacity: 0;
            margin-left: 0.5rem;
        }
        .history-item:hover .history-delete-btn {
            opacity: 0.7;
        }
        .history-delete-btn:hover {
            opacity: 1 !important;
            color: #ff6b6b;
            background: rgba(255, 107, 107, 0.1);
        }
        .history-delete-btn .icon {
            width: 0.8rem;
            height: 0.8rem;
        }
        .history-empty {
            padding: 1rem;
            text-align: center;
            color: var(--text-color);
            font-style: italic;
            opacity: 0.7;
        }
        .history-list::-webkit-scrollbar {
            width: 6px;
        }
        .history-list::-webkit-scrollbar-track {
            background: var(--code-background);
        }
        .history-list::-webkit-scrollbar-thumb {
            background: var(--hover-color);
            border-radius: 3px;
        }
        .history-list::-webkit-scrollbar-thumb:hover {
            background: var(--secondary-color);
        }
        .loading {
            text-align: center;
            margin: 2rem 0;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid var(--hover-color);
            border-top: 4px solid var(--gfg-green);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .profile-results { margin-top: 2rem; }
        .profile-section {
            background: var(--card-background);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid var(--hover-color);
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1rem;
        }
        .profile-header img {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 3px solid var(--gfg-green);
        }
        .profile-section h3 {
            border-bottom: 2px solid var(--gfg-green);
            padding-bottom: 0.5rem;
        }
        .profile-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5rem;
            align-items: stretch;
        }
        .profile-card {
            background: var(--hover-color);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 150px;
        }
        .profile-card h4 {
            margin: 0 0 1rem 0;
            font-size: 0.9rem;
            font-weight: 400;
            color: var(--text-color);
            text-transform: uppercase;
        }
        .card-value {
            color: var(--secondary-color);
            font-size: 2.2rem;
            font-weight: 700;
        }
        .card-value.institute-text {
            font-size: 1.1rem;
            line-height: 1.4;
            font-weight: 500;
        }
        .error-message {
            background: #ff6b6b;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            margin: 1rem 0;
        }
        .endpoint {
            background: var(--card-background);
            border-radius: 12px;
            margin: 1.5rem 0;
            border: 1px solid var(--hover-color);
            overflow: hidden;
        }
        .endpoint-header {
            padding: 1.5rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .endpoint-header:hover { background-color: var(--hover-color); }
        .endpoint-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.35s ease-out;
            padding: 0 1.5rem;
        }
        .endpoint.active .endpoint-content {
            max-height: 5000px;
            padding: 0 1.5rem 1.5rem;
        }
        .endpoint-toggle {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--secondary-color);
            transition: transform 0.3s ease;
        }
        .endpoint.active .endpoint-toggle { transform: rotate(45deg); }
        code {
            background: var(--code-background);
            color: var(--secondary-color);
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
        }
        pre {
            background: var(--code-background);
            padding: 1.5rem;
            border-radius: 12px;
            overflow-x: auto;
            margin: 1.5rem 0;
            border: 1px solid var(--hover-color);
        }
    </style>
</head>
<body>
    <div style="position: fixed; top: 1rem; right: 1rem; z-index: 10; display: flex; gap: 0.5rem;">
        <a href="/docs" class="swagger-link">Swagger UI</a>
        <a href="/redoc" class="swagger-link">ReDoc</a>
    </div>

    <h1>GeeksForGeeks Stats Dashboard</h1>
    <p>Analyze GeeksForGeeks user statistics interactively below.</p>

    <div class="stalker-form">
        <h3>Explore a GeeksForGeeks Profile</h3>
        <div class="input-group">
            <div class="input-container">
                <input type="text" id="gfg-username" placeholder="Enter GFG username (e.g., khantashif)" autocomplete="off" />
                <button type="button" id="clear-history" class="clear-history-btn" title="Clear input">
                    <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
                <div id="history-dropdown" class="history-dropdown">
                    <div class="dropdown-header">
                        <span>Recent Searches</span>
                        <button type="button" id="clear-all-history" class="clear-all-btn" title="Clear all history">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                            </svg>
                        </button>
                    </div>
                    <div id="history-list" class="history-list"></div>
                </div>
            </div>
            <button onclick="stalkGFGUser()" class="stalk-button">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                Analyze
            </button>
        </div>
        <div id="gfg-loading" class="loading" style="display: none;">
            <div class="spinner"></div>
            <p>Fetching GFG data...</p>
        </div>
    </div>

    <div id="gfg-profile-results" class="profile-results" style="display: none;"></div>
    
    <h1>GeeksForGeeks Stats API Documentation</h1>
    <p>This API provides access to GeeksForGeeks user statistics and problem-solving data.</p>
    
    <div class="endpoint">
        <div class="endpoint-header">
            <h2><span style="background-color: var(--gfg-green); color: white; padding: 0.3rem 0.5rem; border-radius: 4px; font-weight: bold; margin-right: 0.5rem;">GET</span> User Statistics</h2>
            <span class="endpoint-toggle">+</span>
        </div>
        <div class="endpoint-content">
            <p><code>/{username}</code></p>
            <h3>Parameters</h3>
            <div><code>username</code> (path parameter): GeeksForGeeks username</div>
            <h3>Response Format</h3>
            <pre><code>{
    "userName": "example_user",
    "totalProblemsSolved": 150,
    "School": 20,
    "Basic": 35,
    "Easy": 50,
    "Medium": 30,
    "Hard": 15
}</code></pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="endpoint-header">
            <h2><span style="background-color: var(--gfg-green); color: white; padding: 0.3rem 0.5rem; border-radius: 4px; font-weight: bold; margin-right: 0.5rem;">GET</span> User Profile</h2>
            <span class="endpoint-toggle">+</span>
        </div>
        <div class="endpoint-content">
            <p><code>/{username}/profile</code></p>
            <h3>Parameters</h3>
            <div><code>username</code> (path parameter): GeeksForGeeks username</div>
            <h3>Response Format</h3>
            <pre><code>{
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
}</code></pre>
        </div>
    </div>

    <div class="endpoint">
        <div class="endpoint-header">
            <h2><span style="background-color: var(--gfg-green); color: white; padding: 0.3rem 0.5rem; border-radius: 4px; font-weight: bold; margin-right: 0.5rem;">GET</span> Solved Problems</h2>
            <span class="endpoint-toggle">+</span>
        </div>
        <div class="endpoint-content">
            <p><code>/{username}/solved-problems</code></p>
            <h3>Parameters</h3>
            <div><code>username</code> (path parameter): GeeksForGeeks username</div>
            <h3>Response Format</h3>
            <pre><code>{
    "userName": "example_user",
    "totalProblemsSolved": 150,
    "problems": [
        { "question": "Two Sum", "questionUrl": "...", "difficulty": "easy" }
    ]
}</code></pre>
        </div>
    </div>

    <footer>
        <p>This API is open source and available on <a href="https://github.com/tashifkhan/GFG-Stats-API" style="color: var(--gfg-green); text-decoration: none;">GitHub</a>.</p>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const endpoints = document.querySelectorAll('.endpoint');
            endpoints.forEach(endpoint => {
                const header = endpoint.querySelector('.endpoint-header');
                header.addEventListener('click', () => {
                    endpoint.classList.toggle('active');
                });
            });

            const input = document.getElementById('gfg-username');
            if (input) {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        stalkGFGUser();
                    }
                });

                input.addEventListener('focus', function() {
                    showDropdown();
                });
                
                document.addEventListener('click', function(e) {
                    const inputContainer = document.querySelector('.input-container');
                    if (!inputContainer.contains(e.target)) {
                        hideDropdown();
                    }
                });
            }
            updateHistoryDropdown();
            
            const clearBtn = document.getElementById('clear-history');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    document.getElementById('gfg-username').value = '';
                });
            }

            const clearAllBtn = document.getElementById('clear-all-history');
            if (clearAllBtn) {
                clearAllBtn.addEventListener('click', clearUserHistory);
            }
        });

        async function stalkGFGUser() {
            const username = document.getElementById('gfg-username').value.trim();
            if (!username) {
                alert('Please enter a GeeksForGeeks username.');
                return;
            }
            
            saveUserHistory(username);

            const loading = document.getElementById('gfg-loading');
            const resultsContainer = document.getElementById('gfg-profile-results');
            loading.style.display = 'block';
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';

            try {
                const [statsRes, profileRes] = await Promise.all([
                    fetch(`/${username}`),
                    fetch(`/${username}/profile`)
                ]);

                if (!statsRes.ok || !profileRes.ok) {
                    const errorJson = await (statsRes.ok ? profileRes.json() : statsRes.json());
                    throw new Error(errorJson.message || 'User not found or API error.');
                }
                
                const stats = await statsRes.json();
                const profile = await profileRes.json();

                displayGFGProfileResults(stats, profile);
                resultsContainer.style.display = 'block';

            } catch (error) {
                resultsContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
                resultsContainer.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }

        function displayGFGProfileResults(stats, profile) {
            const container = document.getElementById('gfg-profile-results');
            container.innerHTML = `
                <div class="profile-section">
                    <div class="profile-header">
                        <img src="${profile.profilePicture}" alt="Profile Picture">
                        <div>
                            <h3 style="margin: 0; padding: 0; border: none;">${profile.fullName || profile.userName}</h3>
                            <p style="margin: 0; color: var(--text-color);">${profile.userName}</p>
                        </div>
                    </div>
                    <div class="profile-cards">
                        <div class="profile-card"><h4>Institute</h4><div class="card-value institute-text">${profile.institute || '-'}</div></div>
                        <div class="profile-card"><h4>Institute Rank</h4><div class="card-value">${profile.instituteRank || '-'}</div></div>
                        <div class="profile-card"><h4>Coding Score</h4><div class="card-value">${profile.codingScore || 0}</div></div>
                        <div class="profile-card"><h4>Current Streak</h4><div class="card-value">${profile.currentStreak || 0}</div></div>
                        <div class="profile-card"><h4>Max Streak</h4><div class="card-value">${profile.maxStreak || 0}</div></div>
                    </div>
                </div>
                <div class="profile-section">
                    <h3>Problem Stats (Total: ${stats.totalProblemsSolved})</h3>
                    <div style="height: 300px;"><canvas id="difficulty-chart"></canvas></div>
                </div>
            `;
            
            const ctx = document.getElementById('difficulty-chart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['School', 'Basic', 'Easy', 'Medium', 'Hard'],
                    datasets: [{
                        label: 'Problems Solved',
                        data: [stats.School, stats.Basic, stats.Easy, stats.Medium, stats.Hard],
                        backgroundColor: ['#4ade80', '#38bdf8', '#60a5fa', '#facc15', '#f87171'],
                        borderColor: 'rgba(0,0,0,0)',
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: { 
                        y: { 
                            beginAtZero: true,
                            ticks: { 
                                color: '#ccd6f6', 
                                font: { 
                                    family: "'SF Mono', 'Fira Code', 'Monaco', monospace",
                                    size: 14
                                } 
                            },
                            grid: { color: 'rgba(136, 146, 176, 0.1)' }
                        },
                        x: {
                            ticks: { 
                                color: '#ccd6f6', 
                                font: { 
                                    family: "'SF Mono', 'Fira Code', 'Monaco', monospace",
                                    size: 14
                                } 
                            },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        const USER_HISTORY_KEY = 'gfg_username_history';
        const MAX_HISTORY_ITEMS = 10;

        function loadUserHistory() {
            try {
                const history = localStorage.getItem(USER_HISTORY_KEY);
                return history ? JSON.parse(history) : [];
            } catch (error) {
                console.error('Error loading user history:', error);
                return [];
            }
        }

        function saveUserHistory(username) {
            if (!username || username.trim() === '') return;
            
            try {
                let history = loadUserHistory();
                const usernameLower = username.toLowerCase().trim();
                
                history = history.filter(item => item.toLowerCase() !== usernameLower);
                
                history.unshift(username.trim());
                
                const trimmedHistory = history.slice(0, MAX_HISTORY_ITEMS);
                
                localStorage.setItem(USER_HISTORY_KEY, JSON.stringify(trimmedHistory));
                updateHistoryDropdown();
            } catch (error) {
                console.error('Error saving user history:', error);
            }
        }

        function updateHistoryDropdown() {
            const historyList = document.getElementById('history-list');
            const history = loadUserHistory();
            
            if (!historyList) return;
            
            historyList.innerHTML = '';
            
            if (history.length === 0) {
                historyList.innerHTML = '<div class="history-empty">No recent searches</div>';
                return;
            }
            
            history.forEach((username, index) => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.innerHTML = `
                    <span class="history-username">${username}</span>
                    <button type="button" class="history-delete-btn" data-index="${index}" title="Remove from history">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                        </svg>
                    </button>
                `;
                
                item.addEventListener('click', (e) => {
                    if (!e.target.closest('.history-delete-btn')) {
                        document.getElementById('gfg-username').value = username;
                        hideDropdown();
                        stalkGFGUser();
                    }
                });
                
                const deleteBtn = item.querySelector('.history-delete-btn');
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    removeFromHistory(index);
                });
                
                historyList.appendChild(item);
            });
        }

        function showDropdown() {
            const dropdown = document.getElementById('history-dropdown');
            if (dropdown) {
                dropdown.classList.add('active');
            }
        }

        function hideDropdown() {
            const dropdown = document.getElementById('history-dropdown');
            if (dropdown) {
                dropdown.classList.remove('active');
            }
        }

        function removeFromHistory(index) {
            try {
                const history = loadUserHistory();
                history.splice(index, 1);
                localStorage.setItem(USER_HISTORY_KEY, JSON.stringify(history));
                updateHistoryDropdown();
            } catch (error) {
                console.error('Error removing from history:', error);
            }
        }

        function clearUserHistory() {
            try {
                localStorage.removeItem(USER_HISTORY_KEY);
                updateHistoryDropdown();
                hideDropdown();
            } catch (error) {
                console.error('Error clearing user history:', error);
            }
        }
    </script>
</body>
</html>
"""


@docs_router.get("/", response_class=HTMLResponse, tags=["Documentation"])
async def get_custom_documentation():
    """
    Serves the custom HTML API documentation page with an interactive dashboard.
    """
    return HTMLResponse(content=docs_html_content)


@docs_router.get("/docs", include_in_schema=False)
async def get_swagger_ui_redirect():
    return RedirectResponse(url="/docs")


@docs_router.get("/redoc", include_in_schema=False)
async def get_redoc_redirect():
    return RedirectResponse(url="/redoc")
