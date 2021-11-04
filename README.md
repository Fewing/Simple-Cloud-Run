# Simple-Cloud-Run
A toy PaaS service

## db(sqlite)

```sql
CREATE TABLE USER(
	ID INTEGER PRIMARY KEY,
  NAME VARCHAR(20) NOT NULL,
  PASSWORD VARCHAR(30) NOT NULL
);

CREATE TABLE APP(  
    id INTEGER NOT NULL primary key,
    user_id INTEGER NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    containers VARCHAR(255) NOT NULL
);
```

