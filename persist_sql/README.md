# Persistant SQLite Database on Cloud Workspaces 

As a data science enthusiast, I have been using Lightning AI for my analytics and upskilling. It’s a great and cost-effective platform, but I’ve often faced one major limitation—the absence of SQL Server or any other persistent database.

This isn’t just a Lightning AI issue; it’s a common challenge with Google Colab, Codespaces, and other cloud workspaces. One common workaround is using SQLite, but there’s a catch—since cloud workspaces are ephemeral, all data is lost after every session, forcing me to recreate tables from scratch each time.

In Lightning AI, I could reuse the same database file within the same studio, but what if I wanted to access it across different studios? While there is a way around this, it’s neither easy nor straightforward.

Exploring Alternatives

I considered using AWS RDS or Azure Databases, but they are expensive and not ideal for someone using them for personal projects or learning.

The Solution: Persistent SQL Database for Cloud Workspaces

To address this, I built a python module 'persistent-sql' that allows users to maintain a persistent SQL database in cloud environments using:
✅ SQLite Database for local queries
✅ AWS S3 Bucket for persistent storage

How to Use - 
1. pip install persistent-sql
2. import persistent-sql as ps
	ps.configure_aws(AWS_KEY, AWS_SECRET, AWS_BUCKET_NAME) 
	ps.connect_db('DEV')
	%sql select * from tablename
	ps.close_connection()

Limitations & Considerations

🔹 This works best when your database size is small.
🔹 If your data grows significantly, consider splitting tables across multiple database files to optimize performance.

GitHub Repository & Demo Notebook

I have shared sample notebook demonstrating how to use this solution. Feel free to explore, contribute, and share your feedback! 🚀