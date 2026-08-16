-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: store2
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `people`
--

DROP TABLE IF EXISTS `people`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `people` (
  `people_id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `password_hash` varchar(200) NOT NULL,
  `birth_date` date NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address` varchar(100) NOT NULL,
  `city` varchar(50) NOT NULL,
  `role` enum('MANAGER','EMPLOYEE','CUSTOMER') NOT NULL,
  PRIMARY KEY (`people_id`),
  UNIQUE KEY `phone` (`phone`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people`
--

LOCK TABLES `people` WRITE;
/*!40000 ALTER TABLE `people` DISABLE KEYS */;
INSERT INTO `people` VALUES (1,'Farzad','Asadi','$argon2id$v=19$m=65536,t=3,p=4$tuxBFI7lOlwZCcBG+fQeyg$wx2PyTQM7RpLNdkI4zQK30/qpUxYrUc31TdoYEUzleU','1995-10-18','09131234567','Khaghany street','Tehran','MANAGER'),(3,'Farzaneh','Mohammadi','$argon2id$v=19$m=65536,t=3,p=4$HOsjfeM2IsCbGPoQXb+E3A$ErpQkzR90sXIcU6/78wis9CaKnmEMxhZiqhsC7MpRgo','1990-08-15','09894860141','Mir street','Isfahan','CUSTOMER'),(4,'Sara','Rahmani','$argon2id$v=19$m=65536,t=3,p=4$DfXAqDDwZ45ULbHDiAoZAQ$mkUbLR0ii9IPVAF7Nc3LHXq6+8G1+MTF+VkSzRy8wTs','1995-11-16','09328172578','Azadi street','Isfahan','CUSTOMER'),(5,'Mohammad','Kaviani','$argon2id$v=19$m=65536,t=3,p=4$7CPSn3SZ3oy9DXSrxT6W8Q$dbYa0tv9I5svH6gEsCK5UCmEREia9Egl1md+JRwfDFw','2000-08-25','09282199740','Azadi street','Isfahan','CUSTOMER'),(6,'Sadaf','Ahmadi','$argon2id$v=19$m=65536,t=3,p=4$xie0YDeOeBb4z2LdgALyfw$XxXmUfV4hJwjoRdtfBIe3G94hcC7AZyKZI6fcUE/ALQ','1998-05-08','09868466475','Enghelab street','Isfahan','EMPLOYEE'),(8,'Yousef','Moradi','$argon2id$v=19$m=65536,t=3,p=4$hFyZNN62oIebmoxAIevstQ$3mMYxSWaU4PnVJwbpbx1jjc1H2XSQbErk0PUKXRvqOU','2002-10-19','09868469897','Kaveh street','Shiraz','EMPLOYEE'),(10,'Nima','Falahi','$argon2id$v=19$m=65536,t=3,p=4$QQ+ITsbD5mHCSkJ5BZXjyA$G2cKhqt2pQl1pFafNa3uO0CmyA2LV68SMccgBiiFJfw','1995-11-12','09404608567','Mir stret','Yazd','EMPLOYEE'),(11,'Parvaneh','Hosseini','$argon2id$v=19$m=65536,t=3,p=4$Pm/3Px/YvDf7Aitr5gXKZg$59NKGcrXE+jH4ewiSFqUh4RsfAupmHXl7UwdXKZVa7Y','2000-08-15','09925835391','Nazar street','Isfahan','EMPLOYEE'),(12,'Farid','Ahmadi','$argon2id$v=19$m=65536,t=3,p=4$2JvNyhKuU0FnMahxRrYuLw$gHPrkSnoR1wYJhwGzpCbu/cf4taw9eWCxY5zhXNjhzU','1955-08-10','09556720769','Mir street','Isfahan','CUSTOMER'),(13,'Nazanin','Farahmand','$argon2id$v=19$m=65536,t=3,p=4$skT5tiAJh9dQxUKG3Y/dPw$KtG3FvTIsTTkMaH32fL/2cjRu0n6MPUTl1+KFA/V4cM','1999-08-22','09984921014','Nazar street','Isfahan','CUSTOMER'),(15,'Sara','Goli','$argon2id$v=19$m=65536,t=3,p=4$25BZZVVJkSiCNAdB7J1npA$3H10EOxjZ8c6LVfUDIidqinkADRoN/QvzZeEK1YP6fw','1999-08-22','09984921015','Nazar street','Isfahan','CUSTOMER'),(16,'Yalda','Hazer','$argon2id$v=19$m=65536,t=3,p=4$b5w/6CeJIvVkiKmY1515Ug$uY0ynS8THmZCgYlM0J6BocssWoQbuF+vmkfK4O4AiT4','1999-08-22','09984921987','Nazar street','Isfahan','EMPLOYEE');
/*!40000 ALTER TABLE `people` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-16 12:12:33
