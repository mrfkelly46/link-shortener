DELIMITER //
DROP PROCEDURE IF EXISTS updateLink //

CREATE PROCEDURE updateLink(IN linkID int, IN new_original varchar(512))
BEGIN

  UPDATE links
  SET
    original_link=new_original
  WHERE
    id=linkID;

END //
DELIMITER ;

