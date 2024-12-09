-- MySQL Script generated by MySQL Workbench
-- Sun Dec  1 18:16:13 2024
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';


USE `telegram_bot_shop` ;

-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`categories`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`categories` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`products`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`products` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `price` INT NOT NULL,
  `category_id` INT NULL DEFAULT NULL,
  `description` TEXT NULL DEFAULT NULL,
  `image` VARCHAR(255) NULL DEFAULT NULL,
  `link` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `category_id` (`category_id` ASC) VISIBLE,
  CONSTRAINT `products_ibfk_1`
    FOREIGN KEY (`category_id`)
    REFERENCES `telegram_bot_shop`.`categories` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`cart`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`cart` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NULL DEFAULT NULL,
  `product_id` INT NOT NULL,
  `quantity` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `product_id` (`product_id` ASC) VISIBLE,
  CONSTRAINT `cart_ibfk_1`
    FOREIGN KEY (`product_id`)
    REFERENCES `telegram_bot_shop`.`products` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 40
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`orders`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`orders` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NULL DEFAULT NULL,
  `total_price` INT NOT NULL,
  `status` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 38
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`order_details`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`order_details` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  `quantity` INT NOT NULL,
  `price_per_unit` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `order_id` (`order_id` ASC) VISIBLE,
  INDEX `product_id` (`product_id` ASC) VISIBLE,
  CONSTRAINT `order_details_ibfk_1`
    FOREIGN KEY (`order_id`)
    REFERENCES `telegram_bot_shop`.`orders` (`id`),
  CONSTRAINT `order_details_ibfk_2`
    FOREIGN KEY (`product_id`)
    REFERENCES `telegram_bot_shop`.`products` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `telegram_bot_shop`.`product_categories`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `telegram_bot_shop`.`product_categories` (
  `product_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  PRIMARY KEY (`product_id`, `category_id`),
  INDEX `category_id` (`category_id` ASC) VISIBLE,
  CONSTRAINT `product_categories_ibfk_1`
    FOREIGN KEY (`product_id`)
    REFERENCES `telegram_bot_shop`.`products` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `product_categories_ibfk_2`
    FOREIGN KEY (`category_id`)
    REFERENCES `telegram_bot_shop`.`categories` (`id`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;