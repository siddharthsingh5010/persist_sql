# Persistant SQLite Database on Cloud Workspaces 

As a data science enthusiast, I have been using Lightning AI for my analytics and upskilling. It’s a great and cost-effective platform, but I’ve often faced one major limitation—the absence of SQL Server or any other persistent database.

This isn’t just a Lightning AI issue; it’s a common challenge with Google Colab, Codespaces, and other cloud workspaces. One common workaround is using SQLite, but there’s a catch—since cloud workspaces are ephemeral, all data is lost after every session, forcing me to recreate tables from scratch each time.

In Lightning AI, I could reuse the same database file within the same studio, but what if I wanted to access it across different studios? While there is a way around this, it’s neither easy nor straightforward.

Exploring Alternatives

I considered using AWS RDS or Azure Databases, but they are expensive and not ideal for someone using them for personal projects or learning.

The Solution: Persistent SQL Database for Cloud Workspaces

To address this, I built a solution that allows users to maintain a persistent SQL database in cloud environments using:
✅ SQLite Database for local queries
✅ AWS S3 Bucket for persistent storage

How It Works
	•	The solution saves your SQLite database file in an S3 bucket, enabling you to restore it across different cloud sessions.
	•	Simply provide your AWS credentials as environment variables, and it will handle database creation and restoration automatically.

Limitations & Considerations

🔹 This works best when your database size is small.
🔹 If your data grows significantly, consider splitting tables across multiple database files to optimize performance.

GitHub Repository & Demo Notebook

I have shared the GitHub repo below, which includes a sample notebook demonstrating how to use this solution. Feel free to explore, contribute, and share your feedback! 🚀

Would love to hear your thoughts! How do you manage databases in cloud workspaces? Let’s discuss in the comments. 👇