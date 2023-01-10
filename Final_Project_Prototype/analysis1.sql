CREATE DEFINER=`root`@`localhost` PROCEDURE `analysis_1`(IN minsetsize INT,
                                 IN min_age DOUBLE, IN max_age DOUBLE)
BEGIN
    SELECT Lastname AS last_name, 
    count(*) AS set_size, 
    count(distinct passengerClass) AS class_count, 
    avg(age)
    FROM titanicsurvival
    WHERE age IS NOT NULL
    AND age BETWEEN min_age AND max_age
    GROUP BY Lastname HAVING set_size >= minsetsize
    ORDER BY Lastname;
END