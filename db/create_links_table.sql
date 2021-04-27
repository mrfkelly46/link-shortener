DROP TABLE IF EXISTS links;
CREATE TABLE links (
  id int NOT NULL AUTO_INCREMENT,
  original_link varchar(512) NOT NULL,
  shortened_link varchar(64) NOT NULL UNIQUE,
  users_id int,
  PRIMARY KEY (id)
);

