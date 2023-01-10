CREATE DEFINER=`root`@`localhost` PROCEDURE `analysis_2`(IN min_subset_size INT, IN start_letter varchar(1),
							  IN min_age DOUBLE, IN max_age DOUBLE)
BEGIN
    SELECT Lastname AS last_name, LEFT(passengerClass, 1) as class, count(*) as subset_size, avg(age)
    FROM titanicsurvival
    WHERE age IS NOT NULL
    AND age BETWEEN min_age AND max_age
    AND LEFT(Lastname, 1) = start_letter
    GROUP BY Lastname, LEFT(passengerClass, 1) HAVING subset_size >= min_subset_size
    ORDER BY Lastname;
END