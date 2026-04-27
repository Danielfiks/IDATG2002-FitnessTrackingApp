-- --------------------------------------------------------
-- Table structure for table `User`
-- --------------------------------------------------------
CREATE TABLE `User` (
  `UserID` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) DEFAULT NULL,
  `Email` varchar(150) NOT NULL UNIQUE,
  `Password` varchar(150) NOT NULL,
  `Age` int(3) DEFAULT NULL,
  `Gender` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `Workout`
-- --------------------------------------------------------
CREATE TABLE `Workout` (
  `WorkoutID` int(11) NOT NULL AUTO_INCREMENT,
  `UserID` int(11) NOT NULL,
  `WorkoutType` varchar(50) NOT NULL,
  `Date` date DEFAULT NULL,
  `Duration` int(11) DEFAULT NULL,
  PRIMARY KEY (`WorkoutID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `Workout_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `ExerciseEntry`
-- --------------------------------------------------------
CREATE TABLE `ExerciseEntry` (
  `EntryID` int(11) NOT NULL AUTO_INCREMENT,
  `WorkoutID` int(11) NOT NULL,
  `ExerciseName` varchar(100) NOT NULL,
  `Sets` int(3) DEFAULT NULL,
  `Reps` int(3) DEFAULT NULL,
  `Weight` int(3) DEFAULT NULL,
  PRIMARY KEY (`EntryID`),
  KEY `WorkoutID` (`WorkoutID`),
  CONSTRAINT `ExerciseEntry_ibfk_1` FOREIGN KEY (`WorkoutID`) REFERENCES `Workout` (`WorkoutID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `Goal`
-- --------------------------------------------------------
CREATE TABLE `Goal` (
  `GoalID` int(11) NOT NULL AUTO_INCREMENT,
  `UserID` int(11) NOT NULL,
  `GoalType` varchar(200) NOT NULL,
  `TargetValue` int(11) NOT NULL,
  `StartDate` date NOT NULL,
  `EndDate` date DEFAULT NULL,
  `Status` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`GoalID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `Goal_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `HealthMetric`
-- --------------------------------------------------------
CREATE TABLE `HealthMetric` (
  `MetricID` int(11) NOT NULL AUTO_INCREMENT,
  `UserID` int(11) NOT NULL,
  `MetricType` varchar(100) NOT NULL,
  `MetricValue` int(11) NOT NULL,
  `RecordedDate` date NOT NULL,
  PRIMARY KEY (`MetricID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `HealthMetric_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `Progress`
-- --------------------------------------------------------
CREATE TABLE `Progress` (
  `ProgressID` int(11) NOT NULL AUTO_INCREMENT,
  `UserID` int(11) NOT NULL,
  `GoalID` int(11) NOT NULL,
  `ProgressValue` int(11) NOT NULL,
  `RecordedDate` date NOT NULL,
  PRIMARY KEY (`ProgressID`),
  KEY `UserID` (`UserID`),
  KEY `GoalID` (`GoalID`),
  CONSTRAINT `Progress_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `Progress_ibfk_2` FOREIGN KEY (`GoalID`) REFERENCES `Goal` (`GoalID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;