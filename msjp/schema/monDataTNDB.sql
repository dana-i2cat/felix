SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

-- --------------------------------------------------------

--
-- DATABASE: `monDataTNDB`
--
DROP DATABASE IF EXISTS `monDataTNDB`;
CREATE DATABASE `monDataTNDB` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `monDataTNDB`;

-- --------------------------------------------------------

--
-- TABLE `metaData`
--

DROP TABLE IF EXISTS `metaData`;
CREATE TABLE IF NOT EXISTS `metaData` (
  `metaID` int(11) NOT NULL AUTO_INCREMENT,
  `network_name` varchar(255) NOT NULL,
  `link_name` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  PRIMARY KEY (`metaID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- TABLE `data`
--

DROP TABLE IF EXISTS `data`;
CREATE TABLE IF NOT EXISTS `data` (
  `metaID` int(11) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `value` int(11) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`metaID`,`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
