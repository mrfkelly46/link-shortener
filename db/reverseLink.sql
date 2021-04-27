DELIMITER //
DROP PROCEDURE IF EXISTS reverseLink //

CREATE PROCEDURE reverseLink(IN shortened varchar(64))
BEGIN

  SELECT original_link FROM links WHERE shortened_link=shortened;
  
END //
DELIMITER ;

