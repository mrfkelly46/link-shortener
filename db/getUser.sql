DELIMITER //
DROP PROCEDURE IF EXISTS getUser //

CREATE PROCEDURE getUser(IN user_name varchar(64))
BEGIN

  INSERT IGNORE INTO users (username) VALUES (user_name);
  SELECT * FROM users WHERE username=user_name;

END //
DELIMITER ;

