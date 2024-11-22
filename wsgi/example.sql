-- Table: post_tags
CREATE TABLE post_tags (
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Table: users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activation_key VARCHAR(80),
    date_joined DATETIME,
    email VARCHAR(150) NOT NULL,
    email_alerts BOOLEAN,
    followers TEXT,
    following TEXT,
    karma INTEGER,
    openid VARCHAR(80),
    password VARCHAR(80),
    receive_email BOOLEAN,
    role INTEGER,
    username VARCHAR(60) NOT NULL
);

-- Table: posts
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access INTEGER,
    author_id INTEGER NOT NULL,
    date_created DATETIME,
    description TEXT,
    link VARCHAR(250),
    num_comments INTEGER,
    score INTEGER,
    tags TEXT,
    title VARCHAR(200),
    votes TEXT,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: comments
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    comment TEXT,
    date_created DATETIME,
    parent_id INTEGER,
    post_id INTEGER NOT NULL,
    score INTEGER,
    votes TEXT,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- Table: tags
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80),
    slug VARCHAR(80)
);

-- Relationships:
-- Relationship between posts and post_tags
-- Already defined in post_tags table with FOREIGN KEYs.

-- Relationship between tags and post_tags
-- Already defined in post_tags table with FOREIGN KEYs.

-- Relationship between users and posts
-- Already defined in posts table with FOREIGN KEY (author_id).

-- Relationship between users and comments
-- Already defined in comments table with FOREIGN KEY (author_id).

-- Relationship between posts and comments
-- Already defined in comments table with FOREIGN KEY (post_id).

-- Relationship between comments and comments (self-referencing)
-- Already defined in comments table with FOREIGN KEY (parent_id).
