SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

-- --------------------------------------------------------

--
-- DATABASE: `monTopologyDB`
--
DROP DATABASE IF EXISTS `monTopologyDB`;
CREATE DATABASE `monTopologyDB` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `monTopologyDB`;

-- --------------------------------------------------------

--
-- TABLE `M_NETWORK`
--

DROP TABLE IF EXISTS `M_NETWORK`;
CREATE TABLE IF NOT EXISTS `M_NETWORK` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(32) NOT NULL,
  `registration_time` int(11) NOT NULL,
  `last_update_time` int(11) NOT NULL,
  `network_name` varchar(255) NOT NULL,
  `user` varchar(255) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- TABLE `M_NODE`
--

DROP TABLE IF EXISTS `M_NODE`;
CREATE TABLE IF NOT EXISTS `M_NODE` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(32) NOT NULL,
  `network_name` varchar(255) NOT NULL,
  `node_name` varchar(255) NOT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- TABLE `M_NODE_INFO`
--

DROP TABLE IF EXISTS `M_NODE_INFO`;
CREATE TABLE IF NOT EXISTS `M_NODE_INFO` (
  `idNode` int(11) NOT NULL,
  `vkey` varchar(255) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idNode`,`vkey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- TABLE `M_NODE_MGMT`
--

DROP TABLE IF EXISTS `M_NODE_MGMT`;
CREATE TABLE IF NOT EXISTS `M_NODE_MGMT` (
  `idNode` int(11) NOT NULL,
  `vkey` varchar(255) NOT NULL,
  `type` varchar(10) NOT NULL,
  `address` varchar(48),
  `port` varchar(8),
  `auth` varchar(255),
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idNode`,`vkey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- TABLE `M_VM_MAPPING`
--

DROP TABLE IF EXISTS `M_VM_MAPPING`;
CREATE TABLE IF NOT EXISTS `M_VM_MAPPING` (
  `idServer` int(11) NOT NULL,
  `idVM` int(11) NOT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idServer`,`idVM`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- TABLE `M_IF`
--

DROP TABLE IF EXISTS `M_IF`;
CREATE TABLE IF NOT EXISTS `M_IF` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idNode` int(11) NOT NULL,
  `if_name` varchar(255) NOT NULL,
  `port` varchar(255) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- TABLE `M_IF_INFO`
--

DROP TABLE IF EXISTS `M_IF_INFO`;
CREATE TABLE IF NOT EXISTS `M_IF_INFO` (
  `idIF` int(11) NOT NULL,
  `vkey` varchar(255) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idIF`,`vkey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- TABLE `M_LINK`
--

DROP TABLE IF EXISTS `M_LINK`;
CREATE TABLE IF NOT EXISTS `M_LINK` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `src_idIF` int(11) DEFAULT NULL,
  `dst_idIF` int(11) DEFAULT NULL,
  `type` varchar(32) NOT NULL,
  `network_name` varchar(255) NOT NULL,
  `link_name` varchar(255) DEFAULT NULL,
  `abst_idLink` int(11) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- TABLE `M_LINK_INFO`
--

DROP TABLE IF EXISTS `M_LINK_INFO`;
CREATE TABLE IF NOT EXISTS `M_LINK_INFO` (
  `idLink` int(11) NOT NULL,
  `vkey` varchar(255) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  `dbUpdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idLink`,`vkey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
