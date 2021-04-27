DELIMITER //
DROP PROCEDURE IF EXISTS addLink //

CREATE PROCEDURE addLink(IN userID int, IN original varchar(512), IN shortened varchar(64))
BEGIN

  INSERT INTO links (users_id, original_link, shortened_link) VALUES (userID, original, shortened);

  IF (row_count() = 0) THEN
    SIGNAL SQLSTATE '52711'
      SET message_text = 'Unable to create the link.';
  END IF;

  SELECT last_insert_id() AS new_id;

END //
DELIMITER ;

