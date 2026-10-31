# SmartSpend AI

A chat app that tries to spend less on AI. Every AI answer costs money, and the bigger the model, the more it costs. But most questions are simple and don't need the biggest model. So this app checks each question and sends it to the cheapest model that can handle it.

## What it does
- Sends simple questions to a small AI model and harder ones to a bigger model
- Shows why it picked that model, how many tokens were used and what it cost
- Remembers answers, so repeated or similar questions don't cost anything
- Has a daily budget. Once it's used up, the app switches to the cheaper model
- Tries the other model if one fails, and asks the bigger model if the small one isn't sure
- Has a stats page with charts showing cost, cache hits and how much was saved
- Login for me, and a limited guest demo for anyone who wants to try it

## Built with
React, FastAPI (Python), SQLite, Groq API, JWT and bcrypt for login, Recharts for the charts

## What I learned
- How a React frontend and a FastAPI backend talk to each other, and why CORS matters
- How tokens, models and pricing work when you use an AI API
- How to keep secrets out of code, and how login with JWT works
- Fixing problems after going live, like a model being retired and CORS errors

## Things I know are limited
- The cache is stored in memory, so it resets when the server restarts
- The free hosting resets the database sometimes, so old stats can disappear
- Costs are estimates from Groq's public prices, because the free tier doesn't actually charge me
- The cache matches similar questions by comparing keywords, not by meaning
