-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: iis_db
-- ------------------------------------------------------
-- Server version	8.0.45

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
-- Table structure for table `access_requests`
--

DROP TABLE IF EXISTS `access_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `access_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_name` varchar(150) NOT NULL,
  `industry` varchar(100) NOT NULL,
  `company_size` varchar(50) NOT NULL,
  `contact_person` varchar(150) NOT NULL,
  `work_email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `position_title` varchar(100) NOT NULL,
  `contact_number` varchar(50) NOT NULL,
  `notes` text,
  `status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  `reviewed_by` int DEFAULT NULL,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `rejection_reason` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `work_email` (`work_email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access_requests`
--

LOCK TABLES `access_requests` WRITE;
/*!40000 ALTER TABLE `access_requests` DISABLE KEYS */;
INSERT INTO `access_requests` VALUES (1,'Virtualahan Incorporated ','Information Technology','201-500 employees','Jinalie C. Arbuis','intern3@virtualahan.com','','Skills Incubator','09531080123','09531080123','pending',NULL,NULL,NULL,'2026-04-23 06:28:47'),(2,'Jinah Corporation','Manufacturing','51-200 employees','Maria','jinah@testemail.com','scrypt:32768:8:1$xMn09DKAZ7q5RmDm$c061c6dff8ede97f2bbf16392cc3f03ddc3def8cb9b9288ea84fbaa7b1aa43a1d2ffd0fae7f0f8c1bc0af8c61054dc390829e75fab34d6ff59749bb7d48edf1c','Skills Incubator','12345678910','12345678910','pending',NULL,NULL,NULL,'2026-04-23 09:26:57');
/*!40000 ALTER TABLE `access_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assessment_answers`
--

DROP TABLE IF EXISTS `assessment_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessment_answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assessment_id` int NOT NULL,
  `question_id` int NOT NULL,
  `selected_choice_id` int NOT NULL,
  `score_value` decimal(5,2) NOT NULL,
  `saved_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_assessment_question` (`assessment_id`,`question_id`),
  KEY `fk_answer_question` (`question_id`),
  KEY `fk_answer_choice` (`selected_choice_id`),
  CONSTRAINT `fk_answer_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_answer_choice` FOREIGN KEY (`selected_choice_id`) REFERENCES `question_choices` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_answer_question` FOREIGN KEY (`question_id`) REFERENCES `question_bank` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assessment_answers`
--

LOCK TABLES `assessment_answers` WRITE;
/*!40000 ALTER TABLE `assessment_answers` DISABLE KEYS */;
/*!40000 ALTER TABLE `assessment_answers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assessment_dimensions`
--

DROP TABLE IF EXISTS `assessment_dimensions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessment_dimensions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assessment_dimensions`
--

LOCK TABLES `assessment_dimensions` WRITE;
/*!40000 ALTER TABLE `assessment_dimensions` DISABLE KEYS */;
INSERT INTO `assessment_dimensions` VALUES (1,'Hiring','Inclusive hiring practices'),(2,'Onboarding','Inclusive onboarding processes'),(3,'Accommodation','Workplace accommodation readiness'),(4,'Retention','Retention and support practices'),(5,'Culture','Inclusion culture and belonging');
/*!40000 ALTER TABLE `assessment_dimensions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assessments`
--

DROP TABLE IF EXISTS `assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `organization_id` int NOT NULL,
  `assessment_type` enum('baseline','reassessment') NOT NULL DEFAULT 'baseline',
  `status` enum('draft','submitted','completed') NOT NULL DEFAULT 'draft',
  `cycle_number` int NOT NULL DEFAULT '1',
  `overall_score` decimal(5,2) DEFAULT NULL,
  `maturity_level` enum('Emerging','Developing','Advancing','Leading','Exemplar') DEFAULT NULL,
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `submitted_at` timestamp NULL DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_assessment_organization` (`organization_id`),
  CONSTRAINT `fk_assessment_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assessments`
--

LOCK TABLES `assessments` WRITE;
/*!40000 ALTER TABLE `assessments` DISABLE KEYS */;
/*!40000 ALTER TABLE `assessments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `benchmark_snapshots`
--

DROP TABLE IF EXISTS `benchmark_snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `benchmark_snapshots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assessment_id` int NOT NULL,
  `network_average_score` decimal(5,2) DEFAULT NULL,
  `top_performer_score` decimal(5,2) DEFAULT NULL,
  `organization_rank` int DEFAULT NULL,
  `eligible_org_count` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_benchmark_assessment` (`assessment_id`),
  CONSTRAINT `fk_benchmark_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `benchmark_snapshots`
--

LOCK TABLES `benchmark_snapshots` WRITE;
/*!40000 ALTER TABLE `benchmark_snapshots` DISABLE KEYS */;
/*!40000 ALTER TABLE `benchmark_snapshots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dimension_scores`
--

DROP TABLE IF EXISTS `dimension_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dimension_scores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assessment_id` int NOT NULL,
  `dimension_id` int NOT NULL,
  `score` decimal(5,2) NOT NULL,
  `severity_flag` enum('none','moderate','critical') NOT NULL DEFAULT 'none',
  `raw_score` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_assessment_dimension` (`assessment_id`,`dimension_id`),
  KEY `fk_dimension_score_dimension` (`dimension_id`),
  CONSTRAINT `fk_dimension_score_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dimension_score_dimension` FOREIGN KEY (`dimension_id`) REFERENCES `assessment_dimensions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dimension_scores`
--

LOCK TABLES `dimension_scores` WRITE;
/*!40000 ALTER TABLE `dimension_scores` DISABLE KEYS */;
/*!40000 ALTER TABLE `dimension_scores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `email_notifications`
--

DROP TABLE IF EXISTS `email_notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `email_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `organization_id` int DEFAULT NULL,
  `assessment_id` int DEFAULT NULL,
  `notification_type` enum('account_approval','account_rejection','account_activation','reassessment_reminder','password_reset','report_ready') NOT NULL,
  `recipient_email` varchar(150) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `message_body` text,
  `send_status` enum('pending','sent','failed') NOT NULL DEFAULT 'pending',
  `sent_at` timestamp NULL DEFAULT NULL,
  `error_message` text,
  `triggered_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_email_user` (`user_id`),
  KEY `fk_email_org` (`organization_id`),
  KEY `fk_email_assessment` (`assessment_id`),
  KEY `fk_email_triggered_by` (`triggered_by`),
  CONSTRAINT `fk_email_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_email_org` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_email_triggered_by` FOREIGN KEY (`triggered_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_email_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `email_notifications`
--

LOCK TABLES `email_notifications` WRITE;
/*!40000 ALTER TABLE `email_notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `email_notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fellow_journey_tracking`
--

DROP TABLE IF EXISTS `fellow_journey_tracking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fellow_journey_tracking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fellow_id` int NOT NULL,
  `organization_id` int NOT NULL,
  `assessment_id` int DEFAULT NULL,
  `status` enum('on_track','at_risk','offboarded') NOT NULL,
  `notes` text,
  `tracked_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_fjt_fellow` (`fellow_id`),
  KEY `fk_fjt_org` (`organization_id`),
  KEY `fk_fjt_assessment` (`assessment_id`),
  CONSTRAINT `fk_fjt_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_fjt_fellow` FOREIGN KEY (`fellow_id`) REFERENCES `fellows` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_fjt_org` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fellow_journey_tracking`
--

LOCK TABLES `fellow_journey_tracking` WRITE;
/*!40000 ALTER TABLE `fellow_journey_tracking` DISABLE KEYS */;
/*!40000 ALTER TABLE `fellow_journey_tracking` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fellows`
--

DROP TABLE IF EXISTS `fellows`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fellows` (
  `id` int NOT NULL AUTO_INCREMENT,
  `organization_id` int NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `status` enum('On Track','At Risk') NOT NULL DEFAULT 'On Track',
  `remarks` text,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_fellow_organization` (`organization_id`),
  CONSTRAINT `fk_fellow_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fellows`
--

LOCK TABLES `fellows` WRITE;
/*!40000 ALTER TABLE `fellows` DISABLE KEYS */;
/*!40000 ALTER TABLE `fellows` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gap_flags`
--

DROP TABLE IF EXISTS `gap_flags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gap_flags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assessment_id` int NOT NULL,
  `dimension_id` int NOT NULL,
  `question_id` int DEFAULT NULL,
  `severity` enum('moderate','critical') NOT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_gap_assessment` (`assessment_id`),
  KEY `fk_gap_dimension` (`dimension_id`),
  KEY `fk_gap_question` (`question_id`),
  CONSTRAINT `fk_gap_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_gap_dimension` FOREIGN KEY (`dimension_id`) REFERENCES `assessment_dimensions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_gap_question` FOREIGN KEY (`question_id`) REFERENCES `question_bank` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gap_flags`
--

LOCK TABLES `gap_flags` WRITE;
/*!40000 ALTER TABLE `gap_flags` DISABLE KEYS */;
/*!40000 ALTER TABLE `gap_flags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organizations`
--

DROP TABLE IF EXISTS `organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `organizations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `industry` varchar(100) NOT NULL,
  `size` varchar(50) NOT NULL,
  `status` enum('pending','approved','suspended','rejected') NOT NULL DEFAULT 'pending',
  `approved_at` timestamp NULL DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organizations`
--

LOCK TABLES `organizations` WRITE;
/*!40000 ALTER TABLE `organizations` DISABLE KEYS */;
/*!40000 ALTER TABLE `organizations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `question_bank`
--

DROP TABLE IF EXISTS `question_bank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `question_bank` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dimension_id` int NOT NULL,
  `question_text` text NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `version` int NOT NULL DEFAULT '1',
  `created_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_question_dimension` (`dimension_id`),
  KEY `fk_question_created_by` (`created_by`),
  CONSTRAINT `fk_question_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_question_dimension` FOREIGN KEY (`dimension_id`) REFERENCES `assessment_dimensions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `question_bank`
--

LOCK TABLES `question_bank` WRITE;
/*!40000 ALTER TABLE `question_bank` DISABLE KEYS */;
INSERT INTO `question_bank` VALUES (1,1,'How are your job postings designed to attract candidates with disabilities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(2,1,'How accessible is your job application process to candidates with disabilities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(3,1,'What measures are in place to prevent disability bias during candidate screening',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(4,1,'How does your organization ensure interviews are accessible and bias-free for PWD candidates?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(5,1,'How does your organization ensure job selection criteria that do not unfairly exclude PWD candidates?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(6,1,'Does your organozation set and track hiring targets for persons with disabilities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(7,1,'Does your organization source candidates with disabilities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(8,1,'How are pre-employment assessments (tests, tasks, exercises) made accessibleto PWd candidates?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(9,1,'How does, your organization handle the offer stage to ensure it is inclusive for PWD candidates?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(10,1,'How does your organization track and use hiring data related to disability inclusion?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(11,2,'How does your organization prepare for the arrival of a PWD new hire before their first day?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(12,2,'How accessible are your orientation and onboarding materials to employees with disabilities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(13,2,'Does your organization assign a buddy or mentor to PWD new hires during the onboarding period?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(14,2,'How quickly are accommodation needs addressed when identified during the onboarding period?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(15,2,'Are managers trained and prepared to onboard an employee with a disability?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(16,2,'How does your organization ensure PWD new hires have clear role expectations and performance goals from Day 1?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(17,2,'How does your organization ensure the physical workplace orientation is accessible to all PWD new hires?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(18,2,'How does your organization ensure PWD new hires can access all required digital systems and tools from Day 1?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(19,2,'How does your organization introduce PWD new hires to their team in an inclusive way?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(20,2,'How does your organization monitor the experience of PWD new hires during onboarding?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(21,3,'Does your organization have a formal, written workplace accommodation policy?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(22,3,'How clear and accessible is the process for employees to request a workplace accommodation?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(23,3,'What is your organization\'s typical response time from accommodation request to resolution?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(24,3,'Are managers trained to receive and act on accommodation requests without bias?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(25,3,'What percentage of your office spaces are physically accessible to employees with mobility impairments?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(26,3,'Are the digital tools your employees use daily audited for accessibility compliance??',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(27,3,'How does your organization support employees who need assistive technology (screen readers, voice recognition, ergonomic equipment, etc.)?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(28,3,'How does your organization use flexible or remote work as an accommodation option for PWD employees?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(29,3,'How does your organization protect the confidentiality and dignity of employees who disclose a disability or request accommodation?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(30,3,'How does your organization review the effectiveness of accommodations already in place?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(31,4,'How does your organization\'s voluntary attrition rate for PWD employees compare to the overall employee attrition rate?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(32,4,'How does your organization ensure PWD employees have equitable access to career development and growth opportunities?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(33,4,'Are PWD employees promoted at a rate equitable to their non-PWD peers at comparable performance levels?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(34,4,'How does your organization ensure the performance management process is fair and accessible to PWD employees?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(35,4,'Does your organization provide mentoring or sponsorship programs accessible to and inclusive of PWD employees?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(36,4,'How does your organization use exit interview data to understand and reduce PWD employee turnover?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(37,4,'How does your organization support PWD employees returning after a health-related or disability-related absence?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(38,4,'How safe do PWD employees feel raising concerns, requesting accommodations, or disclosing disability status?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(39,4,'How does your organization ensure PWD employees are included in team activities, informal networks, and social events?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(40,4,'How does your organization demonstrate a long-term commitment to retaining PWD employees beyond initial placement?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(41,5,'How visibly do senior leaders champion disability inclusion in your organization?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(42,5,'Does your organization have a formal Disability Inclusion or DEI policy that specifically addresses disability?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(43,5,'How does your organization promote and enforce inclusive, respectful language about disability?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(44,5,'What disability awareness training do all employees receive?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(45,5,'Does your organization have an ERG or affinity group for PWD employees and disability allies?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(46,5,'How does your organization mark disability awareness moments (e.g., International Day of Persons with Disabilities)?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(47,5,'How does your organization collect and act on feedback from PWD employees about the workplace culture?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(48,5,'How does your organization extend its disability inclusion values to its supply chain and partners??',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(49,5,'How does your organization celebrate and recognize the contributions of PWD employees?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32'),(50,5,'How does your organization measure and continuously improve its disability inclusion culture?',1,1,NULL,'2026-04-20 08:04:32','2026-04-20 08:04:32');
/*!40000 ALTER TABLE `question_bank` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `question_choices`
--

DROP TABLE IF EXISTS `question_choices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `question_choices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `choice_letter` enum('A','B','C','D') NOT NULL,
  `choice_text` varchar(255) NOT NULL,
  `choice_score` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_question_choice` (`question_id`,`choice_letter`),
  CONSTRAINT `fk_choice_question` FOREIGN KEY (`question_id`) REFERENCES `question_bank` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=201 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `question_choices`
--

LOCK TABLES `question_choices` WRITE;
/*!40000 ALTER TABLE `question_choices` DISABLE KEYS */;
INSERT INTO `question_choices` VALUES (1,1,'A','All postings explicitly welcome PWD applicants, state available accommodations, and are published on disability-inclusive job platforms.',4.00),(2,1,'B','Most postings include an equal opportunity statement and mention accommodation availability upon request.',3.00),(3,1,'C','We include a generic equal opportunity clause but do not actively communicate accommodation availability.',2.00),(4,1,'D','Job postings do not address disability inclusion or accommodation in any way.',1.00),(5,2,'A','Application process is fully accessible (WCAG 2.1 AA), tested with assistive technology, and offers multiple submission formats (online, email, phone).',4.00),(6,2,'B','Application is online and largely accessible; we offer alternative formats when specifically requested.',3.00),(7,2,'C','Application is online but has not been audited for accessibility; accommodations are handled case by case.',2.00),(8,2,'D','No accessibility audit has been done; we are unaware of any barriers in our application process.',1.00),(9,3,'A','Blind CV screening is standard; disability disclosure fields are removed before review; structured scoring rubrics are used by all reviewers.',4.00),(10,3,'B','We use structured rubrics and have trained screeners on unconscious bias, but disability details are still visible on CVs.',3.00),(11,3,'C','We have general unconscious bias training but no specific disability-focused screening protocols.',2.00),(12,3,'D','No structured screening process or bias-prevention measures are in place.',1.00),(13,4,'A','All interviewers receive disability inclusion training; candidates are proactively asked about accommodation needs before the interview; structured interview questions are used consistently.',4.00),(14,4,'B','We ask candidates about accommodations upon request and use structured questions, but interviewer training is not mandatory.',3.00),(15,4,'C','Accommodations are provided if a candidate asks, but we do not proactively offer them; interviewer training is ad-hoc.',2.00),(16,4,'D','No accommodation process for interviews; interviewers receive no disability-specific training.',1.00),(17,5,'A','All job requirements are reviewed for essential vs. non-essential functions; criteria are validated against actual job demands; adjustments are made where requirements can be met with reasonable accommodation.',4.00),(18,5,'B','HR reviews criteria for obvious exclusionary requirements but no formal validation process exists.',3.00),(19,5,'C','Selection criteria are set by hiring managers with no formal review for disability-related exclusion.',2.00),(20,5,'D','Selection criteria have never been reviewed through a disability inclusion lens.',1.00),(21,6,'A','We have formal, quantified PWD hiring targets, report progress quarterly, and link targets to leadership accountability.',4.00),(22,6,'B','We have informal hiring targets for PWDs and track progress annually.',3.00),(23,6,'C','We are aware of the need for PWD hiring targets but have not formally set them.',2.00),(24,6,'D','We have no hiring targets related to disability inclusion.',1.00),(25,7,'A','We have active partnerships with at least 3 disability-focused organizations (e.g., Virtualahan), attend disability job fairs, and maintain relationships with PWD communities.',4.00),(26,7,'B','We partner with 1–2 disability organizations and occasionally attend relevant job fairs.',3.00),(27,7,'C','We rely on general job boards and accept referrals from disability organizations when they come to us.',2.00),(28,7,'D','We have no active sourcing strategy targeting candidates with disabilities.',1.00),(29,8,'A','Assessments are designed to be disability-neutral by default, offered in accessible formats, and alternative assessment methods are available for all roles.',4.00),(30,8,'B','Accessible formats are available upon request and we adjust assessments case by case.',3.00),(31,8,'C','We make adjustments when a candidate specifically requests them, but our default assessments are not designed with accessibility in mind.',2.00),(32,8,'D','Pre-employment assessments have not been reviewed for accessibility.',1.00),(33,9,'A','Offer process includes proactive discussion of accommodation needs, flexible start dates, and documentation of agreed support before the first day.',4.00),(34,9,'B','We discuss accommodations during the offer stage when a candidate raises it.',3.00),(35,9,'C','Accommodations are discussed during onboarding, not the offer stage.',2.00),(36,9,'D','Accommodation needs are not formally discussed at any stage of the hiring process.',1.00),(37,10,'A','We collect voluntary disability disclosure data, track PWD hiring rates, analyze pipeline conversion at each stage, and report findings to leadership quarterly.',4.00),(38,10,'B','We collect voluntary disclosure data and track overall PWD hiring numbers annually.',3.00),(39,10,'C','We collect voluntary disclosure data but do not analyze it systematically.',2.00),(40,10,'D','We do not collect or track any disability-related hiring data.',1.00),(41,11,'A','A structured pre-boarding checklist is completed for every PWD hire: workstation assessed, assistive technology installed, buddy assigned, and all access needs confirmed in writing.',4.00),(42,11,'B','We confirm accommodation needs before Day 1 and make basic preparations, but no formal checklist is used.',3.00),(43,11,'C','We prepare for PWD new hires on a case-by-case basis with no standard process.',2.00),(44,11,'D','No specific pre-boarding preparation is made for PWD new hires beyond standard onboarding.',1.00),(45,12,'A','All orientation materials (documents, videos, presentations) meet WCAG 2.1 AA standards, are available in multiple formats (screen-reader friendly, captioned, large print), and have been tested by a PWD.',4.00),(46,12,'B','Most materials are in digital format and generally accessible; we provide alternative formats upon request.',3.00),(47,12,'C','Materials are in standard digital formats that have not been audited for accessibility.',2.00),(48,12,'D','Orientation materials are print-based or use formats that have not been reviewed for accessibility.',1.00),(49,13,'A','All PWD new hires are assigned a trained inclusion buddy who checks in weekly for the first 90 days; buddy training is mandatory and documented.',4.00),(50,13,'B','We assign a buddy to PWD new hires but buddy training is informal and check-ins are not structured.',3.00),(51,13,'C','A buddy is assigned to all new hires (not PWD-specific); no specialized preparation for supporting PWD colleagues.',2.00),(52,13,'D','No buddy or mentor system exists during onboarding.',1.00),(53,14,'A','All accommodation requests raised during onboarding are resolved within 5 business days; a single point of contact (accommodation coordinator) manages the process.',4.00),(54,14,'B','Accommodations are addressed within 2 weeks; HR manages the process but no dedicated coordinator exists.',3.00),(55,14,'C','Accommodations are addressed eventually but with no defined timeline; the process varies by manager.',2.00),(56,14,'D','Accommodation needs raised during onboarding are not tracked or managed systematically.',1.00),(57,15,'A','All managers whose teams include PWD hires complete mandatory disability inclusion and onboarding training before the employee\'s first day; training is assessed and documented.',4.00),(58,15,'B','Managers receive disability awareness training as part of general management development, but it is not specifically timed to a PWD hire.',3.00),(59,15,'C','Training is available but optional; not all relevant managers have completed it.',2.00),(60,15,'D','Managers receive no specific training on onboarding employees with disabilities.',1.00),(61,16,'A','Structured 30-60-90 day plans are co-created with every new hire including PWDs; plans explicitly account for any adjustment period and are reviewed by HR.',4.00),(62,16,'B','30-60-90 day plans are used for most new hires; PWD-specific adjustments are made when raised.',3.00),(63,16,'C','Role expectations are communicated verbally; no structured written plan is standard.',2.00),(64,16,'D','New hires are expected to figure out role expectations through observation and informal guidance.',1.00),(65,17,'A','A personalized physical orientation is conducted for every PWD new hire, covering all accessible routes, facilities, emergency evacuation procedures (with personalized plan), and assistive equipment locations.',4.00),(66,17,'B','Physical orientation covers main areas; personalized accessibility routes are shown when needed.',3.00),(67,17,'C','Standard workplace tour is provided to all new hires with no disability-specific adaptation.',2.00),(68,17,'D','No formal workplace orientation is provided.',1.00),(69,18,'A','All required systems are pre-configured for accessibility before the employee\'s start date; IT conducts a personalized accessibility setup session within the first week',4.00),(70,18,'B','Standard IT setup is completed before Day 1; accessibility settings are configured when the employee requests them.',3.00),(71,18,'C','IT setup is completed, but accessibility configurations are left to the employee to figure out.',2.00),(72,18,'D','IT setup is often delayed for new hires; no accessibility review of digital tools is done.',1.00),(73,19,'A','Team introductions follow a structured inclusion protocol: team is briefed on respectful communication before the new hire arrives; introduction formats are agreed with the new hire in advance.',4.00),(74,19,'B','Team introductions happen naturally; managers remind teams of respectful communication principles informally',3.00),(75,19,'C','New hires are introduced to teams at the manager\'s discretion with no structured protocol',2.00),(76,19,'D','No specific approach to team introductions for PWD new hires exists.',1.00),(77,20,'A','Structured check-ins occur at Day 7, Day 30, and Day 90 with both HR and the line manager; feedback is documented and any concerns trigger a formal response process.',4.00),(78,20,'B','At least one formal HR check-in occurs within the first 30 days for PWD new hires.',3.00),(79,20,'C','Manager check-ins happen informally; no structured HR review of the onboarding experience.',2.00),(80,20,'D','No formal check-in process exists; issues surface only when the employee raises them.',1.00),(81,21,'A','A comprehensive written accommodation policy exists, is reviewed annually, is accessible on the company intranet, and is communicated to all employees during onboarding.',4.00),(82,21,'B','A written accommodation policy exists but is not prominently communicated or regularly reviewed.',3.00),(83,21,'C','We follow accommodation practices informally but have no documented policy.',2.00),(84,21,'D','No accommodation policy exists in any form.',1.00),(85,22,'A','A clearly documented, step-by-step accommodation request process is available in multiple accessible formats; employees know exactly who to contact and what to expect at each stage.',4.00),(86,22,'B','A process exists and is documented, but awareness among employees is low.',3.00),(87,22,'C','Employees can request accommodations but must navigate an unclear, inconsistent process.',2.00),(88,22,'D','No formal request process exists; employees must advocate for themselves without guidance.',1.00),(89,23,'A','All requests are acknowledged within 2 business days and fully resolved within 10 business days; response time is tracked and reported.',4.00),(90,23,'B','Most requests are resolved within 3 weeks; response time is not formally tracked.',3.00),(91,23,'C','Resolution typically takes 4–6 weeks and varies significantly by department or manager.',2.00),(92,23,'D','Resolution time is unpredictable and often exceeds 6 weeks or requests are left unresolved.',1.00),(93,24,'A','All managers complete mandatory accommodation training annually; training covers legal obligations, bias awareness, and practical response steps; completion is tracked.',4.00),(94,24,'B','Accommodation training is available and most managers have completed it, but it is not mandatory.',3.00),(95,24,'C','General disability awareness training exists but does not cover accommodation processes specifically.',2.00),(96,24,'D','No accommodation or disability-related training is provided to managers.',1.00),(97,25,'A','100% of office spaces are accessible: accessible entrances, elevators, restrooms, workstations, and emergency evacuation plans for all mobility needs.',4.00),(98,25,'B','75–99% of spaces are accessible; minor gaps exist and are documented with remediation plans.',3.00),(99,25,'C','50–74% of spaces are accessible; significant barriers remain in some areas.',2.00),(100,25,'D','Less than 50% of spaces are accessible or accessibility has not been formally assessed.',1.00),(101,26,'A','All primary digital tools are audited against WCAG 2.1 AA annually; findings are remediated within a defined timeline; accessibility is a procurement requirement for new tools.',4.00),(102,26,'B','Key tools have been assessed for accessibility; gaps are known but remediation is slow.',3.00),(103,26,'C','Some tools have been assessed informally; no systematic audit process exists.',2.00),(104,26,'D','Digital tools have never been assessed for accessibility compliance.',1.00),(105,27,'A','A catalog of available assistive technology is maintained; equipment is provided at no cost to the employee within 5 business days of request; IT provides setup support.',4.00),(106,27,'B','Assistive technology is procured on request; the process works but takes 2–4 weeks.',3.00),(107,27,'C','Assistive technology can be requested but the process is unclear and slow.',2.00),(108,27,'D','No formal process or budget exists for assistive technology procurement.',1.00),(109,28,'A','Flexible and remote work are formally recognized as accommodation options; policies explicitly include these arrangements; they are granted without stigma when requested for disability-related reasons.',4.00),(110,28,'B','Flexible/remote work is available as an accommodation but requires manager approval on a case-by-case basis.',3.00),(111,28,'C','Flexible/remote work is theoretically available but not commonly granted as an accommodation.',2.00),(112,28,'D','Flexible/remote work is not recognized as a formal accommodation option.',1.00),(113,29,'A','Strict confidentiality protocols are in place: disclosure is shared only with those with operational need to know; consent is obtained before any sharing; employees are trained on their rights.',4.00),(114,29,'B','Confidentiality is maintained by HR but protocols are not formally documented or communicated to employees.',3.00),(115,29,'C','Confidentiality is expected but not formally governed; practices vary by manager.',2.00),(116,29,'D','No formal confidentiality protocols exist for disability disclosure or accommodation requests.',1.00),(117,30,'A','Accommodations are reviewed at least annually in partnership with the employee; reviews are documented and adjustments are made proactively as roles or needs change.',4.00),(118,30,'B','Accommodations are reviewed when the employee raises a concern or when a role changes.',3.00),(119,30,'C','Accommodations are rarely reviewed after initial implementation unless a problem arises.',2.00),(120,30,'D','No review process exists; accommodations, once implemented, are never formally revisited.',1.00),(121,31,'A','PWD voluntary attrition is at or below the overall organizational attrition rate; data is tracked quarterly and any gap triggers an immediate review.',4.00),(122,31,'B','PWD attrition is slightly higher (up to 10% above org average) and is monitored annually.',3.00),(123,31,'C','PWD attrition is 10–25% higher than org average; the gap is known but no formal intervention plan exists.',2.00),(124,31,'D','PWD attrition is more than 25% above org average, or attrition is not tracked by disability status at all.',1.00),(125,32,'A','PWD employees participate in career development programs at the same rate as non-PWD peers; participation is tracked; any gap triggers targeted outreach.',4.00),(126,32,'B','Career development opportunities are available to all employees; PWD participation is not specifically tracked.',3.00),(127,32,'C','PWD employees have access to standard career development programs but face informal barriers (scheduling, format, awareness).',2.00),(128,32,'D','Career development access for PWD employees is not monitored; disparities are likely but unconfirmed.',1.00),(129,33,'A','Promotion rates for PWD employees are tracked and benchmarked against non-PWD peers; any gap is formally investigated and remediated.',4.00),(130,33,'B','Promotion rates are not broken down by disability status but the process is designed to be objective.',3.00),(131,33,'C','We believe promotions are equitable but have no data to confirm or deny disparities.',2.00),(132,33,'D','We have not analyzed promotion equity by disability status and disparities may exist.',1.00),(133,34,'A','Performance frameworks are reviewed for disability-related bias annually; accommodation needs are factored into goal-setting; managers are trained on equitable performance evaluation for PWD employees.',4.00),(134,34,'B','Standard performance management applies to all employees; managers are aware of the need to factor in accommodations but receive no formal training.',3.00),(135,34,'C','Performance management is standardized; no specific adjustments or bias reviews for PWD employees.',2.00),(136,34,'D','Performance management has not been reviewed for accessibility or PWD-related equity.',1.00),(137,35,'A','A formal mentoring program exists, actively recruits PWD participants, includes disability-aware mentor training, and tracks PWD participation rates.',4.00),(138,35,'B','A mentoring program exists and is open to all; PWD employees can participate but are not specifically targeted or tracked.',3.00),(139,35,'C','Informal mentoring exists through personal networks; no structured program is in place',2.00),(140,35,'D','No mentoring or sponsorship program exists in the organization.',1.00),(141,36,'A','Exit interviews are conducted for all departing PWD employees; disability-related turnover reasons are tracked separately; findings are reported to leadership and drive specific retention interventions.',4.00),(142,36,'B','Exit interviews are conducted for all employees; disability-related trends are occasionally reviewed.',3.00),(143,36,'C','Exit interviews are conducted but disability status is not captured or analyzed separately.',2.00),(144,36,'D','Exit interviews are not conducted consistently or the data is not analyzed.',1.00),(145,37,'A','A formal return-to-work program exists: phased return plans, accommodation review upon return, dedicated HR support, and manager briefing before the employee\'s return date',4.00),(146,37,'B','Return-to-work is handled by HR on a case-by-case basis; some structure exists but it varies.',3.00),(147,37,'C','Returning employees are expected to resume normal duties; informal support is available on request.',2.00),(148,37,'D','No formal return-to-work process exists; employees return without structured support.',1.00),(149,38,'A','Regular anonymous surveys measure psychological safety specifically for PWD employees; results are reviewed by leadership; any decline triggers immediate action.',4.00),(150,38,'B','General employee satisfaction surveys include some inclusion questions; PWD-specific data is not isolated.',3.00),(151,38,'C','We believe the environment is safe but have no data or formal mechanism to measure it.',2.00),(152,38,'D','No mechanism exists to measure psychological safety for PWD employees.',1.00),(153,39,'A','All team events and social activities are reviewed for accessibility before scheduling; PWD employees are consulted; inaccessible events are adapted or alternatives are offered.',4.00),(154,39,'B','Accessibility of team events is considered but not systematically reviewed; gaps are addressed when flagged.',3.00),(155,39,'C','Team events default to standard formats; PWD employees must raise accessibility concerns themselves.',2.00),(156,39,'D','Accessibility of social and team activities is not considered in planning.',1.00),(157,40,'A','Retention of PWD employees is a stated organizational goal with named executive ownership; 12-month and 24-month retention rates for PWD employees are tracked and reported.',4.00),(158,40,'B','PWD retention is valued informally; some tracking occurs but no formal goal or executive accountability exists.',3.00),(159,40,'C','Retention of PWD employees is discussed but treated as the responsibility of the immediate manager only.',2.00),(160,40,'D','No specific focus on long-term retention of PWD employees exists at an organizational level.',1.00),(161,41,'A','Senior leaders publicly champion disability inclusion through visible actions (internal communications, participation in disability awareness events, public statements); inclusion is a standing agenda item at leadership meetings.',4.00),(162,41,'B','Some senior leaders champion inclusion informally; it is raised occasionally at leadership level.',3.00),(163,41,'C','Disability inclusion is delegated entirely to HR; senior leaders are supportive in principle but not visibly active.',2.00),(164,41,'D','Disability inclusion is not a leadership priority and is rarely mentioned by senior leaders.',1.00),(165,42,'A','A formal, disability-specific inclusion policy exists, is reviewed annually, is accessible to all employees, and has named accountability (e.g., a DEI officer or committee).',4.00),(166,42,'B','A general DEI policy exists that mentions disability; it is accessible but rarely reviewed.',3.00),(167,42,'C','A generic equal opportunity policy exists; disability is implied but not specifically addressed.',2.00),(168,42,'D','No formal DEI or disability inclusion policy exists.',1.00),(169,43,'A','An inclusive language guide specific to disability is available; managers are trained to address non-inclusive language immediately; the guide is reviewed and updated annually.',4.00),(170,43,'B','General communication guidelines exist that touch on respectful language; no disability-specific guidance.',3.00),(171,43,'C','Inclusive language is encouraged informally but there is no formal guidance or enforcement mechanism.',2.00),(172,43,'D','No guidance on inclusive language related to disability exists.',1.00),(173,44,'A','All employees complete mandatory disability awareness training annually; training covers respectful language, allyship, unconscious bias, and practical inclusion behaviors; completion is tracked.',4.00),(174,44,'B','Disability awareness training is available and most employees have completed it, but it is not mandatory.',3.00),(175,44,'C','Training is available but participation is low; it is not promoted or tracked.',2.00),(176,44,'D','No disability awareness training is provided to general employees.',1.00),(177,45,'A','A PWD ERG exists with dedicated budget, executive sponsorship, formal recognition, and regular programming; ERG input is sought in organizational decision-making.',4.00),(178,45,'B','A PWD ERG or informal group exists but has limited budget and no formal executive sponsorship.',3.00),(179,45,'C','Interest in forming a PWD ERG has been expressed but no group has been established.',2.00),(180,45,'D','No ERG or affinity group related to disability exists.',1.00),(181,46,'A','Annual disability awareness programming is planned and resourced; includes internal events, PWD speaker series, and employee communications; outcomes are measured.',4.00),(182,46,'B','The organization marks key awareness dates with internal communications and occasional events.',3.00),(183,46,'C','Awareness dates are acknowledged informally by some teams but not organizationally.',2.00),(184,46,'D','Disability awareness events or dates are not recognized by the organization.',1.00),(185,47,'A','Disaggregated PWD employee feedback is collected through regular surveys; results are shared transparently; action plans are developed and tracked publicly.',4.00),(186,47,'B','General employee surveys include inclusion questions; PWD-specific results are not isolated or shared.',3.00),(187,47,'C','Feedback is collected informally; no mechanism exists to capture disability-specific cultural feedback.',2.00),(188,47,'D','No formal mechanism exists to collect feedback from PWD employees.',1.00),(189,48,'A','Disability inclusion standards are embedded in supplier and partner selection criteria; partners are assessed and encouraged to adopt similar inclusion practices.',4.00),(190,48,'B','We communicate our values to partners and prefer inclusive suppliers when all else is equal.',3.00),(191,48,'C','Our inclusion standards apply internally only; we have not extended them to the supply chain.',2.00),(192,48,'D','Disability inclusion is not considered in supplier or partner relationships.',1.00),(193,49,'A','PWD employee stories and achievements are shared internally with consent; PWD employees are featured in organizational communications, awards, and recognition programs.',4.00),(194,49,'B','PWD employees are recognized through general recognition programs; no specific highlighting of their inclusion journey or contributions.',3.00),(195,49,'C','Recognition programs exist but PWD employees are rarely featured or highlighted.',2.00),(196,49,'D','Recognition programs do not consider disability inclusion perspectives.',1.00),(197,50,'A','Disability inclusion culture is measured annually using a validated instrument; scores are benchmarked against industry peers; a formal improvement plan with named owners and timelines is updated each year.',4.00),(198,50,'B','Cultural inclusion is measured through general engagement surveys; disability-specific trends are reviewed when possible.',3.00),(199,50,'C','We conduct periodic reviews of our culture informally but have no structured measurement tool.',2.00),(200,50,'D','Disability inclusion culture is not formally measured or tracked.',1.00);
/*!40000 ALTER TABLE `question_choices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reports`
--

DROP TABLE IF EXISTS `reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assessment_id` int NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `generated_by` int DEFAULT NULL,
  `generated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_report_assessment` (`assessment_id`),
  KEY `fk_report_generated_by` (`generated_by`),
  CONSTRAINT `fk_report_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_report_generated_by` FOREIGN KEY (`generated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reports`
--

LOCK TABLES `reports` WRITE;
/*!40000 ALTER TABLE `reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `organization_id` int DEFAULT NULL,
  `full_name` varchar(150) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('super_admin','org_admin') NOT NULL,
  `status` enum('pending','approved','inactive') NOT NULL DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `reset_token` varchar(255) DEFAULT NULL,
  `reset_token_expiry` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `fk_users_organization` (`organization_id`),
  CONSTRAINT `fk_users_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-23 17:42:20
