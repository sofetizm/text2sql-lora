# base → lora

Заданий: 120. Исправлено: **6**, сломано: **39**, ошибаются обе: 36.

## Исправлено

### lib-11:ru (hard)

> Выведи имена читателей, у которых на руках больше одной невозвращённой книги.

- эталон: `SELECT r.name FROM readers r JOIN loans l ON l.reader_id = r.reader_id WHERE l.return_date IS NULL GROUP BY r.reader_id HAVING COUNT(*) > 1`
- base: `SELECT DISTINCT r.name FROM readers r JOIN loans l ON r.reader_id = l.reader_id WHERE COUNT(l.loan_id) > 1` (syntax_error)
- lora: `SELECT T1.name FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T2.return_date IS NULL GROUP BY T1.reader_id HAVING COUNT(*) > 1` (верно)

### lib-12:en (easy)

> How many loans were made in 2025?

- эталон: `SELECT COUNT(*) FROM loans WHERE strftime('%Y', loan_date) = '2025'`
- base: `SELECT COUNT(loan_id) FROM loans WHERE YEAR(loan_date) = 2025` (syntax_error)
- lora: `SELECT COUNT(*) FROM loans WHERE loan_date LIKE '2025%'` (верно)

### lib-17:en (hard)

> Books of which genre are borrowed most often? Show only the genre.

- эталон: `SELECT b.genre FROM loans l JOIN books b ON b.book_id = l.book_id GROUP BY b.genre ORDER BY COUNT(*) DESC LIMIT 1`
- base: `SELECT DISTINCT b.genre FROM books AS b JOIN (SELECT book_id, COUNT(*) as num_loans FROM loans GROUP BY book_id) AS l ON b.book_id = l.book_id ORDER BY l.num_loans DESC` (wrong_result)
- lora: `SELECT T3.genre FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id JOIN books AS T3 ON T2.book_id = T3.book_id GROUP BY T3.genre ORDER BY COUNT(*) DESC LIMIT 1` (верно)

### shop-13:ru (medium)

> Выведи имена клиентов, сделавших больше 7 заказов, и количество их заказов.

- эталон: `SELECT c.name, COUNT(*) FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id HAVING COUNT(*) > 7`
- base: `SELECT c.name, COUNT(o.order_id) AS num_orders FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name HAVING COUNT(o.order_id) > 7` (wrong_result)
- lora: `SELECT T1.name, COUNT(*) FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id GROUP BY T1.customer_id HAVING COUNT(*) > 7` (верно)

### uni-14:en (medium)

> List the names of teachers who do not teach any course.

- эталон: `SELECT name FROM teachers WHERE teacher_id NOT IN (SELECT teacher_id FROM courses WHERE teacher_id IS NOT NULL)`
- base: `SELECT DISTINCT t.name FROM teachers AS t JOIN courses AS c ON t.teacher_id = c.teacher_id WHERE c.course_id IS NULL` (wrong_result)
- lora: `SELECT T1.name FROM teachers AS T1 WHERE NOT T1.teacher_id IN (SELECT T2.teacher_id FROM courses AS T2 GROUP BY T2.teacher_id HAVING COUNT(*) > 0)` (верно)

### uni-16:en (hard)

> For each course, count how many students passed it (grade 3 or higher). Show the course title and the count.

- эталон: `SELECT c.title, COUNT(*) FROM courses c JOIN enrollments e ON e.course_id = c.course_id WHERE e.grade >= 3 GROUP BY c.course_id`
- base: `SELECT c.title, COUNT(e.student_id) AS num_students_passed FROM courses c JOIN enrollments e ON c.course_id = e.course_id GROUP BY c.course_id` (wrong_result)
- lora: `SELECT T2.title, COUNT(*) FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id WHERE T1.grade >= 3 GROUP BY T2.title` (верно)

## Сломано

### lib-02:en (easy)

> List the titles of books in the 'Fantasy' genre.

- эталон: `SELECT title FROM books WHERE genre = 'Fantasy'`
- base: `SELECT DISTINCT b.title FROM books AS b JOIN authors AS a ON b.author_id = a.author_id WHERE b.genre = 'Fantasy'` (верно)
- lora: `SELECT T2.title FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id WHERE T1.genre = 'Fantasy'` (schema_error)

### lib-02:ru (easy)

> Выведи названия книг в жанре 'Fantasy'.

- эталон: `SELECT title FROM books WHERE genre = 'Fantasy'`
- base: `SELECT DISTINCT b.title FROM books AS b JOIN authors AS a ON b.author_id = a.author_id WHERE b.genre = 'Fantasy'` (верно)
- lora: `SELECT T2.title FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id WHERE T1.genre = 'Fantasy'` (schema_error)

### lib-03:ru (easy)

> Выведи имена авторов из страны 'Russia'.

- эталон: `SELECT name FROM authors WHERE country = 'Russia'`
- base: `SELECT DISTINCT T1.name FROM authors AS T1 JOIN books AS T2 ON T1.author_id = T2.author_id WHERE T1.country = 'Russia'` (верно)
- lora: `SELECT T1.name FROM authors AS T1 JOIN books AS T2 ON T1.author_id = T2.author_id WHERE T2.country = 'Russia'` (schema_error)

### lib-04:en (easy)

> List the titles of books published before 1950.

- эталон: `SELECT title FROM books WHERE published_year < 1950`
- base: `SELECT b.title FROM books AS b JOIN authors AS a ON b.author_id = a.author_id WHERE b.published_year < 1950` (верно)
- lora: `SELECT T2.title FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T2.loan_date < '1950'` (schema_error)

### lib-05:ru (easy)

> Сколько выдач книг ещё не вернули (дата возврата не указана)?

- эталон: `SELECT COUNT(*) FROM loans WHERE return_date IS NULL`
- base: `SELECT COUNT(*) FROM loans WHERE return_date IS NULL` (верно)
- lora: `SELECT COUNT(*) FROM loans WHERE return_date = 'NULL'` (wrong_result)

### lib-06:en (medium)

> How many books are in each genre? Show the genre and the count.

- эталон: `SELECT genre, COUNT(*) FROM books GROUP BY genre`
- base: `SELECT genre, COUNT(*) FROM books GROUP BY genre` (верно)
- lora: `SELECT T2.genre, COUNT(*) FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id GROUP BY T2.genre` (schema_error)

### lib-06:ru (medium)

> Сколько книг в каждом жанре? Выведи жанр и количество.

- эталон: `SELECT genre, COUNT(*) FROM books GROUP BY genre`
- base: `SELECT genre, COUNT(*) AS count_books FROM books GROUP BY genre` (верно)
- lora: `SELECT T2.genre, COUNT(*) FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id GROUP BY T2.genre` (schema_error)

### lib-08:ru (medium)

> Какое среднее число страниц у книг каждого жанра? Выведи жанр и среднее.

- эталон: `SELECT genre, AVG(pages) FROM books GROUP BY genre`
- base: `SELECT b.genre, AVG(b.pages) as average_pages FROM books b GROUP BY b.genre` (верно)
- lora: `SELECT AVG(T1.pages), T2.genre FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id GROUP BY T2.genre` (schema_error)

### lib-09:ru (medium)

> Выведи имена читателей из города 'Perm', которые брали хотя бы одну книгу.

- эталон: `SELECT DISTINCT r.name FROM readers r JOIN loans l ON l.reader_id = r.reader_id WHERE r.city = 'Perm'`
- base: `SELECT DISTINCT r.name FROM readers AS r JOIN loans AS l ON r.reader_id = l.reader_id WHERE r.city = 'Perm' GROUP BY r.reader_id` (верно)
- lora: `SELECT T1.name FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T2.book_id IN (SELECT T3.book_id FROM books AS T3 JOIN authors AS T4 ON T3.author_id = T4.author_id WHERE T4.country = 'Perm') AND T2.return_date IS NULL` (wrong_result)

### lib-13:en (hard)

> List the names of authors none of whose books has ever been borrowed.

- эталон: `SELECT name FROM authors WHERE author_id NOT IN (SELECT b.author_id FROM books b JOIN loans l ON l.book_id = b.book_id)`
- base: `SELECT DISTINCT a.name FROM authors a WHERE a.author_id NOT IN (SELECT b.author_id FROM books b WHERE b.book_id IN (SELECT l.book_id FROM loans l GROUP BY l.book_id HAVING COUNT(*) > 0))` (верно)
- lora: `SELECT T1.name FROM authors AS T1 JOIN books AS T2 ON T1.author_id = T2.author_id WHERE NOT EXISTS (SELECT * FROM loans AS T3 WHERE T3.book_id = T2.book_id)` (wrong_result)

### lib-18:en (easy)

> List the names of readers who joined the library in 2024.

- эталон: `SELECT name FROM readers WHERE join_year = 2024`
- base: `SELECT T1.name FROM readers AS T1 JOIN readers AS T2 ON T1.reader_id = T2.reader_id WHERE T2.join_year = 2024` (верно)
- lora: `SELECT T1.name FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T2.loan_date LIKE '2024%'` (wrong_result)

### lib-19:ru (easy)

> Сколько книг объёмом больше 500 страниц?

- эталон: `SELECT COUNT(*) FROM books WHERE pages > 500`
- base: `SELECT COUNT(*) FROM books WHERE pages > 500` (верно)
- lora: `SELECT COUNT(*) FROM books AS T1 JOIN loans AS T2 ON T1.book_id = T2.book_id WHERE T1.pages > 500` (wrong_result)

### lib-20:en (hard)

> List the names of readers with at least 10 loans and their number of loans.

- эталон: `SELECT r.name, COUNT(*) FROM readers r JOIN loans l ON l.reader_id = r.reader_id GROUP BY r.reader_id HAVING COUNT(*) >= 10`
- base: `SELECT r.name, COUNT(*) AS num_loans FROM readers r JOIN loans l ON r.reader_id = l.reader_id GROUP BY r.reader_id HAVING COUNT(*) >= 10` (верно)
- lora: `SELECT T2.name, COUNT(*) FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id GROUP BY T1.reader_id HAVING COUNT(*) >= 10` (schema_error)

### lib-20:ru (hard)

> Выведи имена читателей, бравших книги не меньше 10 раз, и число их выдач.

- эталон: `SELECT r.name, COUNT(*) FROM readers r JOIN loans l ON l.reader_id = r.reader_id GROUP BY r.reader_id HAVING COUNT(*) >= 10`
- base: `SELECT DISTINCT r.name, COUNT(*) AS num_loans FROM readers r JOIN loans l ON r.reader_id = l.reader_id GROUP BY r.reader_id HAVING COUNT(l.loan_id) >= 10` (верно)
- lora: `SELECT T2.name, COUNT(*) FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id GROUP BY T1.reader_id HAVING COUNT(*) >= 10` (schema_error)

### shop-02:en (easy)

> List the names of all products in the 'Electronics' category.

- эталон: `SELECT name FROM products WHERE category = 'Electronics'`
- base: `SELECT p.name FROM products AS p JOIN order_items AS oi ON p.product_id = oi.product_id WHERE p.category = 'Electronics'` (верно)
- lora: `SELECT T2.name FROM products AS T1 JOIN order_items AS T2 ON T1.product_id = T2.product_id WHERE T1.category = 'Electronics'` (schema_error)

### shop-02:ru (easy)

> Выведи названия всех товаров категории 'Electronics'.

- эталон: `SELECT name FROM products WHERE category = 'Electronics'`
- base: `SELECT DISTINCT T1.name FROM products AS T1 JOIN order_items AS T2 ON T1.product_id = T2.product_id WHERE T1.category = 'Electronics'` (верно)
- lora: `SELECT T2.name FROM products AS T1 JOIN order_items AS T3 ON T1.product_id = T3.product_id WHERE T1.category = 'Electronics'` (schema_error)

### shop-03:en (easy)

> What is the most expensive product? Show its name and price.

- эталон: `SELECT name, price FROM products ORDER BY price DESC LIMIT 1`
- base: `SELECT p.name, p.price FROM products p ORDER BY p.price DESC LIMIT 1` (верно)
- lora: `SELECT T2.name, T1.price FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id ORDER BY T2.quantity DESC LIMIT 1` (schema_error)

### shop-04:en (easy)

> How many orders have the status 'cancelled'?

- эталон: `SELECT COUNT(*) FROM orders WHERE status = 'cancelled'`
- base: `SELECT COUNT(DISTINCT o.order_id) FROM orders AS o WHERE o.status = 'cancelled'` (верно)
- lora: `SELECT COUNT(*) FROM orders WHERE status = 'Cancelled'` (wrong_result)

### shop-04:ru (easy)

> Сколько заказов имеют статус 'cancelled'?

- эталон: `SELECT COUNT(*) FROM orders WHERE status = 'cancelled'`
- base: `SELECT COUNT(*) FROM orders WHERE status = 'cancelled'` (верно)
- lora: `SELECT COUNT(*) FROM orders WHERE status = 'Cancelled'` (wrong_result)

### shop-05:en (easy)

> What is the average product price?

- эталон: `SELECT AVG(price) FROM products`
- base: `SELECT AVG(products.price) AS average_product_price FROM products` (верно)
- lora: `SELECT AVG(T1.price) FROM products AS T1 JOIN order_items AS T2 ON T1.product_id = T2.product_id WHERE T2.quantity > 0` (wrong_result)

### shop-05:ru (easy)

> Какова средняя цена товара?

- эталон: `SELECT AVG(price) FROM products`
- base: `SELECT AVG(products.price) AS average_price FROM products` (верно)
- lora: `SELECT AVG(t1.price) FROM products AS t1 JOIN order_items AS t2 ON t1.product_id = t2.product_id WHERE t2.quantity > 0 GROUP BY t1.category` (wrong_result)

### shop-06:en (easy)

> List the names of premium customers from the city 'Kazan'.

- эталон: `SELECT name FROM customers WHERE is_premium = 1 AND city = 'Kazan'`
- base: `SELECT DISTINCT c.name FROM customers AS c JOIN orders AS o ON c.customer_id = o.customer_id WHERE c.is_premium = 1 AND c.city = 'Kazan'` (верно)
- lora: `SELECT T1.name FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'completed' AND T1.city = 'Kazan' AND T1.is_premium = 1` (wrong_result)

### shop-06:ru (easy)

> Выведи имена премиум-клиентов из города 'Kazan'.

- эталон: `SELECT name FROM customers WHERE is_premium = 1 AND city = 'Kazan'`
- base: `SELECT DISTINCT c.name FROM customers AS c JOIN orders AS o ON c.customer_id = o.customer_id WHERE c.is_premium = 1 AND c.city = 'Kazan'` (верно)
- lora: `SELECT T1.name FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'completed' AND T1.city = 'Kazan' AND T1.is_premium = 1` (wrong_result)

### shop-07:en (medium)

> How many customers are in each city? Show the city and the count.

- эталон: `SELECT city, COUNT(*) FROM customers GROUP BY city`
- base: `SELECT city, COUNT(*) FROM customers GROUP BY city` (верно)
- lora: `SELECT COUNT(*), T1.city FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id GROUP BY T1.city` (wrong_result)

### shop-07:ru (medium)

> Сколько клиентов в каждом городе? Выведи город и количество.

- эталон: `SELECT city, COUNT(*) FROM customers GROUP BY city`
- base: `SELECT city, COUNT(DISTINCT customer_id) AS count_customers FROM customers GROUP BY city` (верно)
- lora: `SELECT T1.city, COUNT(*) FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id GROUP BY T1.city` (wrong_result)

### shop-10:ru (medium)

> Выведи имена клиентов, которые ни разу не делали заказ.

- эталон: `SELECT name FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders)`
- base: `SELECT DISTINCT c.name FROM customers AS c LEFT JOIN orders AS o ON c.customer_id = o.customer_id WHERE o.order_id IS NULL` (верно)
- lora: `SELECT T1.name FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.order_id IS NULL` (wrong_result)

### shop-11:en (easy)

> How many orders were placed in 2025?

- эталон: `SELECT COUNT(*) FROM orders WHERE strftime('%Y', order_date) = '2025'`
- base: `SELECT COUNT(DISTINCT o.order_id) FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE strftime('%Y', o.order_date) = '2025'` (верно)
- lora: `SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = '2025'` (syntax_error)

### shop-11:ru (easy)

> Сколько заказов было сделано в 2025 году?

- эталон: `SELECT COUNT(*) FROM orders WHERE strftime('%Y', order_date) = '2025'`
- base: `SELECT COUNT(DISTINCT o.order_id) AS num_orders FROM orders o WHERE strftime('%Y', o.order_date) = '2025'` (верно)
- lora: `SELECT COUNT(*) FROM orders WHERE YEAR(order_date) = '2025'` (syntax_error)

### shop-14:en (hard)

> Compute revenue per product category for delivered orders only (status 'delivered'). Show the category and revenue, sorted by revenue descending.

- эталон: `SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.status = 'delivered' GROUP BY p.category ORDER BY revenue DESC`
- base: `SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM products p JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'delivered' GROUP BY p.category ORDER BY revenue DESC` (верно)
- lora: `SELECT T2.category, SUM(T1.quantity * T3.unit_price) AS revenue FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id WHERE T1.status = 'Delivered' GROUP BY T2.category ORDER BY revenue DESC` (schema_error)

### shop-14:ru (hard)

> Посчитай выручку по каждой категории товаров только по доставленным заказам (статус 'delivered'). Выведи категорию и выручку по убыванию выручки.

- эталон: `SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.status = 'delivered' GROUP BY p.category ORDER BY revenue DESC`
- base: `SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id WHERE o.status = 'delivered' GROUP BY p.category ORDER BY revenue DESC` (верно)
- lora: `SELECT T3.category, SUM(T1.quantity * T2.unit_price) FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id WHERE T1.status = 'delivered' GROUP BY T3.category ORDER BY SUM(T1.quantity * T2.unit_price) DESC` (schema_error)

### shop-15:en (hard)

> Which customer spent the most on delivered orders (status 'delivered')? Show the name and the amount.

- эталон: `SELECT c.name, SUM(oi.quantity * oi.unit_price) AS spent FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status = 'delivered' GROUP BY c.customer_id ORDER BY spent DESC LIMIT 1`
- base: `SELECT c.name, SUM(oi.quantity * oi.unit_price) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_items oi ON o.order_id = oi.order_id WHERE o.status = 'delivered' GROUP BY c.customer_id ORDER BY total_spent DESC LIMIT 1` (верно)
- lora: `SELECT T1.name, SUM(T2.quantity * T3.unit_price) FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'Delivered' GROUP BY T1.customer_id ORDER BY SUM(T2.quantity * T3.unit_price) DESC LIMIT 1` (schema_error)

### shop-16:en (medium)

> List the names of products that have never been ordered.

- эталон: `SELECT name FROM products WHERE product_id NOT IN (SELECT product_id FROM order_items)`
- base: `SELECT DISTINCT p.name FROM products AS p LEFT JOIN order_items AS oi ON p.product_id = oi.product_id WHERE oi.order_id IS NULL` (верно)
- lora: `SELECT T1.name FROM products AS T1 JOIN order_items AS T2 ON T1.product_id = T2.product_id WHERE T2.quantity < 0` (wrong_result)

### shop-16:ru (medium)

> Выведи названия товаров, которые ни разу не заказывали.

- эталон: `SELECT name FROM products WHERE product_id NOT IN (SELECT product_id FROM order_items)`
- base: `SELECT DISTINCT p.name FROM products AS p LEFT JOIN order_items AS oi ON p.product_id = oi.product_id WHERE oi.order_id IS NULL` (верно)
- lora: `SELECT T1.name FROM products AS T1 JOIN order_items AS T2 ON T1.product_id = T2.product_id WHERE T2.quantity < 1` (wrong_result)

### uni-02:en (easy)

> List the titles of courses worth more than 4 credits.

- эталон: `SELECT title FROM courses WHERE credits > 4`
- base: `SELECT c.title FROM courses AS c JOIN (SELECT course_id FROM courses WHERE credits > 4) AS cc ON c.course_id = cc.course_id` (верно)
- lora: `SELECT T1.title FROM courses AS T1 JOIN enrollments AS T2 ON T1.course_id = T2.course_id WHERE T1.credits > 4` (wrong_result)

### uni-03:en (easy)

> List the names of students in group 'IT-301'.

- эталон: `SELECT name FROM students WHERE group_name = 'IT-301'`
- base: `SELECT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE s.group_name = 'IT-301'` (верно)
- lora: `SELECT T2.name FROM courses AS T1 JOIN enrollments AS T2 ON T1.course_id = T2.course_id WHERE T2.student_id IN (SELECT student_id FROM students WHERE group_name = 'IT-301')` (schema_error)

### uni-03:ru (easy)

> Выведи имена студентов из группы 'IT-301'.

- эталон: `SELECT name FROM students WHERE group_name = 'IT-301'`
- base: `SELECT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE s.group_name = 'IT-301'` (верно)
- lora: `SELECT T2.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T1.group_name = 'IT-301'` (schema_error)

### uni-05:ru (easy)

> Сколько студентов получают стипендию?

- эталон: `SELECT COUNT(*) FROM students WHERE scholarship = 1`
- base: `SELECT COUNT(DISTINCT student_id) FROM students WHERE scholarship > 0` (верно)
- lora: `SELECT COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.scholarship > 0` (schema_error)

### uni-06:en (medium)

> How many students are in each group? Show the group and the count.

- эталон: `SELECT group_name, COUNT(*) FROM students GROUP BY group_name`
- base: `SELECT group_name, COUNT(DISTINCT student_id) AS num_students FROM students GROUP BY group_name` (верно)
- lora: `SELECT T1.group_name, COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id GROUP BY T1.group_name` (wrong_result)

### uni-19:en (medium)

> List the titles of courses that no student is enrolled in.

- эталон: `SELECT title FROM courses WHERE course_id NOT IN (SELECT course_id FROM enrollments)`
- base: `SELECT c.title FROM courses c WHERE c.course_id NOT IN ( SELECT e.course_id FROM enrollments e ) GROUP BY c.title` (верно)
- lora: `SELECT T1.title FROM courses AS T1 JOIN enrollments AS T2 ON T1.course_id = T2.course_id WHERE NOT EXISTS (SELECT * FROM enrollments AS T3 WHERE T3.student_id = T2.student_id)` (wrong_result)

## Ошибаются обе

### lib-04:ru (easy)

> Выведи названия книг, изданных до 1950 года.

- эталон: `SELECT title FROM books WHERE published_year < 1950`
- base: `SELECT DISTINCT b.title FROM books AS b JOIN authors AS a ON b.author_id = a.author_id WHERE a.birth_year < 1950` (wrong_result)
- lora: `SELECT T2.title FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T2.loan_date < '1950'` (schema_error)

### lib-05:en (easy)

> How many loans have not been returned yet (no return date)?

- эталон: `SELECT COUNT(*) FROM loans WHERE return_date IS NULL`
- base: `SELECT COUNT(*), SUM(CASE WHEN T2.return_date IS NULL THEN 1 ELSE 0 END) AS no_returned_loans FROM loans AS T1 LEFT JOIN readers AS T2 ON T1.reader_id = T2.reader_id` (schema_error)
- lora: `SELECT COUNT(*) FROM loans WHERE return_date = 'NULL'` (wrong_result)

### lib-08:en (medium)

> What is the average number of pages per genre? Show the genre and the average.

- эталон: `SELECT genre, AVG(pages) FROM books GROUP BY genre`
- base: `SELECT AVG(books.pages) AS avg_pages_per_genre, genres.genre FROM books JOIN genres ON books.genre = genres.genre GROUP BY genres.genre` (schema_error)
- lora: `SELECT AVG(T1.pages), T2.genre FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id GROUP BY T2.genre` (schema_error)

### lib-12:ru (easy)

> Сколько выдач книг было в 2025 году?

- эталон: `SELECT COUNT(*) FROM loans WHERE strftime('%Y', loan_date) = '2025'`
- base: `SELECT COUNT(loan_id) FROM loans WHERE YEAR(loan_date) = 2025` (syntax_error)
- lora: `SELECT COUNT(*) FROM loans AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id WHERE T2.published_year = '2025'` (wrong_result)

### lib-13:ru (hard)

> Выведи имена авторов, ни одну книгу которых ни разу не брали.

- эталон: `SELECT name FROM authors WHERE author_id NOT IN (SELECT b.author_id FROM books b JOIN loans l ON l.book_id = b.book_id)`
- base: `SELECT DISTINCT a.name FROM authors a JOIN books b ON a.author_id = b.author_id WHERE b.book_id NOT IN (SELECT book_id FROM loans)` (wrong_result)
- lora: `SELECT T1.name FROM authors AS T1 JOIN books AS T2 ON T1.author_id = T2.author_id WHERE NOT EXISTS (SELECT * FROM loans AS T3 WHERE T3.book_id = T2.book_id)` (wrong_result)

### lib-14:en (medium)

> List the titles of the books published in the earliest year among all books in the library.

- эталон: `SELECT title FROM books WHERE published_year = (SELECT MIN(published_year) FROM books)`
- base: `SELECT b.title FROM books b JOIN (SELECT book_id, MIN(published_year) as min_published_year FROM books GROUP BY book_id) bb ON b.book_id = bb.book_id WHERE b.published_year = bb.min_published_year` (wrong_result)
- lora: `SELECT T1.title FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id ORDER BY T1.published_year LIMIT 1` (wrong_result)

### lib-14:ru (medium)

> Выведи названия книг, изданных в самом раннем году среди всех книг библиотеки.

- эталон: `SELECT title FROM books WHERE published_year = (SELECT MIN(published_year) FROM books)`
- base: `SELECT DISTINCT b.title FROM books AS b JOIN (SELECT book_id, MIN(published_year) as min_published_year FROM books GROUP BY book_id) AS bb ON b.book_id = bb.book_id WHERE b.published_year = bb.min_published_year` (wrong_result)
- lora: `SELECT T1.title FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id ORDER BY T2.birth_year LIMIT 1` (wrong_result)

### lib-15:ru (hard)

> Сколько дней в среднем длится выдача книги? Учитывай только возвращённые книги.

- эталон: `SELECT AVG(julianday(return_date) - julianday(loan_date)) FROM loans WHERE return_date IS NOT NULL`
- base: `SELECT AVG(julian_days(return_date - loan_date)) AS average_loan_duration FROM loans WHERE book_id IN (SELECT book_id FROM books WHERE author_id = (SELECT author_id FROM authors WHERE name = 'Иванов Иван'))` (syntax_error)
- lora: `SELECT AVG(julianday(loan.return_date) - julianday(loan.loan_date)) FROM loans AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id WHERE T2.author_id IN (SELECT author_id FROM authors WHERE country = 'USA') AND T2.genre = 'fiction' AND T2.pages > 500 AND T1.reader_id IN (SELECT reader_id FROM readers WHERE city = 'New York')` (schema_error)

### lib-17:ru (hard)

> Книги какого жанра берут чаще всего? Выведи только жанр.

- эталон: `SELECT b.genre FROM loans l JOIN books b ON b.book_id = l.book_id GROUP BY b.genre ORDER BY COUNT(*) DESC LIMIT 1`
- base: `SELECT DISTINCT T1.genre FROM books AS T1 JOIN (SELECT book_id, COUNT(*) as count FROM loans GROUP BY book_id) AS T2 ON T1.book_id = T2.book_id ORDER BY T2.count DESC LIMIT 1` (wrong_result)
- lora: `SELECT T2.genre FROM readers AS T1 JOIN loans AS T2 ON T1.reader_id = T2.reader_id WHERE T1.city = 'Moscow' GROUP BY T2.genre ORDER BY COUNT(*) DESC LIMIT 1` (schema_error)

### lib-18:ru (easy)

> Выведи имена читателей, которые записались в библиотеку в 2024 году.

- эталон: `SELECT name FROM readers WHERE join_year = 2024`
- base: `SELECT DISTINCT r.name FROM readers AS r JOIN loans AS l ON r.reader_id = l.reader_id WHERE YEAR(l.loan_date) = 2024` (syntax_error)
- lora: `SELECT T3.name FROM loans AS T1 JOIN readers AS T2 ON T1.reader_id = T2.reader_id JOIN books AS T3 ON T1.book_id = T3.book_id WHERE T2.join_year = '2024'` (schema_error)

### shop-03:ru (easy)

> Какой товар самый дорогой? Выведи название и цену.

- эталон: `SELECT name, price FROM products ORDER BY price DESC LIMIT 1`
- base: `SELECT p.name, p.price FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_id ORDER BY oi.quantity DESC LIMIT 1` (wrong_result)
- lora: `SELECT T2.name, T2.price FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id ORDER BY T2.quantity DESC LIMIT 1` (schema_error)

### shop-08:en (medium)

> Which categories have an average product price above 100?

- эталон: `SELECT category FROM products GROUP BY category HAVING AVG(price) > 100`
- base: `SELECT DISTINCT p.category FROM products p WHERE (SELECT AVG(unit_price) FROM order_items oi WHERE oi.product_id = p.product_id) > 100` (wrong_result)
- lora: `SELECT T2.category FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id WHERE T3.price > 100 GROUP BY T2.category` (schema_error)

### shop-08:ru (medium)

> Какие категории имеют среднюю цену товара выше 100?

- эталон: `SELECT category FROM products GROUP BY category HAVING AVG(price) > 100`
- base: `SELECT DISTINCT p.category FROM products p WHERE (SELECT AVG(unit_price) FROM order_items o WHERE o.product_id = p.product_id) > 100` (wrong_result)
- lora: `SELECT T3.category FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id WHERE T2.unit_price > 100 GROUP BY T3.category` (wrong_result)

### shop-09:en (medium)

> What is the total revenue of orders with status 'delivered'? Line revenue is quantity times unit price.

- эталон: `SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'delivered'`
- base: `SELECT SUM(o.quantity * oi.unit_price) AS total_revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE o.status = 'delivered'` (schema_error)
- lora: `SELECT SUM(T1.quantity * T2.unit_price) FROM order_items AS T1 JOIN orders AS T2 ON T1.order_id = T2.order_id WHERE T2.status = 'Delivered'` (schema_error)

### shop-09:ru (medium)

> Какова общая выручка по заказам со статусом 'delivered'? Выручка позиции — количество, умноженное на цену за единицу.

- эталон: `SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'delivered'`
- base: `SELECT SUM(o.quantity * p.price) AS total_revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id WHERE o.status = 'delivered'` (schema_error)
- lora: `SELECT SUM(o.quantity * p.price) FROM orders AS o JOIN order_items AS oi ON o.order_id = oi.order_id JOIN products AS p ON oi.product_id = p.product_id WHERE o.status = 'Delivered'` (schema_error)

### shop-12:ru (hard)

> Выведи 3 товара с наибольшим суммарным количеством проданных единиц: название и количество, по убыванию.

- эталон: `SELECT p.name, SUM(oi.quantity) AS total_qty FROM order_items oi JOIN products p ON p.product_id = oi.product_id GROUP BY p.product_id ORDER BY total_qty DESC LIMIT 3`
- base: `SELECT p.name, o.quantity FROM products p JOIN order_items oi ON p.product_id = oi.product_id WHERE oi.order_id IN ( SELECT order_id FROM orders GROUP BY order_id ORDER BY SUM(oi.quantity) DESC LIMIT 3 ) ORDER BY p.name` (schema_error)
- lora: `SELECT T2.name, SUM(T1.quantity) FROM order_items AS T1 JOIN products AS T2 ON T1.product_id = T2.product_id GROUP BY T1.order_id ORDER BY SUM(T1.quantity) DESC LIMIT 3` (wrong_result)

### shop-15:ru (hard)

> Какой клиент потратил больше всех на доставленные заказы (статус 'delivered')? Выведи имя и сумму.

- эталон: `SELECT c.name, SUM(oi.quantity * oi.unit_price) AS spent FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status = 'delivered' GROUP BY c.customer_id ORDER BY spent DESC LIMIT 1`
- base: `SELECT c.name, SUM(o.quantity * oi.unit_price) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_items oi ON o.order_id = oi.order_id WHERE o.status = 'delivered' GROUP BY c.name ORDER BY total_spent DESC LIMIT 1` (schema_error)
- lora: `SELECT T1.name, SUM(T2.quantity * T3.unit_price) FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'delivered' GROUP BY T1.customer_id ORDER BY SUM(T2.quantity * T3.unit_price) DESC LIMIT 1` (schema_error)

### shop-17:en (hard)

> What percentage of orders have the status 'cancelled'?

- эталон: `SELECT 100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*) FROM orders`
- base: `SELECT CAST(SUM(CASE WHEN T2.status = 'cancelled' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.order_id) FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id` (schema_error)
- lora: `SELECT COUNT(*) * 100 / (SELECT COUNT(*) FROM orders) FROM orders WHERE status = 'Cancelled'` (wrong_result)

### shop-17:ru (hard)

> Какой процент заказов имеет статус 'cancelled'?

- эталон: `SELECT 100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*) FROM orders`
- base: `SELECT (SUM(CASE WHEN T2.status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(T1.order_id)) * 100 AS cancelled_orders_percentage FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id` (schema_error)
- lora: `SELECT COUNT(*) * 100 / (SELECT COUNT(*) FROM orders) FROM orders WHERE status = 'Cancelled'` (wrong_result)

### shop-18:en (hard)

> What is the average order total? An order total is the sum of quantity times unit price over its items.

- эталон: `SELECT AVG(total) FROM (SELECT order_id, SUM(quantity * unit_price) AS total FROM order_items GROUP BY order_id)`
- base: `SELECT AVG(o.quantity * oi.unit_price) AS avg_order_total FROM orders o JOIN order_items oi ON o.order_id = oi.order_id` (schema_error)
- lora: `SELECT AVG(T1.quantity * T2.unit_price) FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id GROUP BY T1.customer_id` (schema_error)

### shop-18:ru (hard)

> Какова средняя сумма одного заказа? Сумма заказа — сумма количества, умноженного на цену за единицу, по всем его позициям.

- эталон: `SELECT AVG(total) FROM (SELECT order_id, SUM(quantity * unit_price) AS total FROM order_items GROUP BY order_id)`
- base: `SELECT AVG(o.quantity * p.price) AS average_order_amount FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id` (schema_error)
- lora: `SELECT AVG(T1.quantity * T2.unit_price) FROM orders AS T1 JOIN order_items AS T2 ON T1.order_id = T2.order_id JOIN products AS T3 ON T2.product_id = T3.product_id GROUP BY T1.customer_id` (schema_error)

### shop-20:en (hard)

> Which city's customers generated the highest revenue from delivered orders (status 'delivered')? Show only the city.

- эталон: `SELECT c.city FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status = 'delivered' GROUP BY c.city ORDER BY SUM(oi.quantity * oi.unit_price) DESC LIMIT 1`
- base: `SELECT T1.city FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'delivered' GROUP BY T1.city ORDER BY SUM(T2.quantity * T3.unit_price) DESC LIMIT 1` (schema_error)
- lora: `SELECT T1.city FROM customers AS T1 JOIN orders AS T2 ON T1.customer_id = T2.customer_id WHERE T2.status = 'Delivered' GROUP BY T1.city ORDER BY SUM(T2.quantity * T3.unit_price) DESC LIMIT 1` (schema_error)

### shop-20:ru (hard)

> В каком городе клиенты принесли наибольшую выручку по доставленным заказам (статус 'delivered')? Выведи только город.

- эталон: `SELECT c.city FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status = 'delivered' GROUP BY c.city ORDER BY SUM(oi.quantity * oi.unit_price) DESC LIMIT 1`
- base: `SELECT T2.city FROM orders AS T1 JOIN customers AS T2 ON T1.customer_id = T2.customer_id WHERE T1.status = 'delivered' GROUP BY T2.city ORDER BY SUM(T1.quantity * T3.unit_price) DESC LIMIT 1` (schema_error)
- lora: `SELECT T3.city FROM orders AS T1 JOIN customers AS T2 ON T1.customer_id = T2.customer_id JOIN order_items AS T4 ON T1.order_id = T4.order_id JOIN products AS T5 ON T4.product_id = T5.product_id WHERE T1.status = 'Delivered' GROUP BY T3.city ORDER BY SUM(T4.quantity * T4.unit_price) DESC LIMIT 1` (schema_error)

### uni-01:en (easy)

> How many students enrolled in 2023?

- эталон: `SELECT COUNT(*) FROM students WHERE enrollment_year = 2023`
- base: `SELECT COUNT(DISTINCT student_id) FROM enrollments WHERE YEAR(enrollment_year) = 2023` (schema_error)
- lora: `SELECT COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.semester = '2023'` (wrong_result)

### uni-02:ru (easy)

> Выведи названия курсов, у которых больше 4 кредитов.

- эталон: `SELECT title FROM courses WHERE credits > 4`
- base: `SELECT c.title FROM courses AS c JOIN enrollments AS e ON c.course_id = e.course_id GROUP BY c.course_id HAVING COUNT(e.student_id) > 4` (wrong_result)
- lora: `SELECT T1.title FROM courses AS T1 JOIN enrollments AS T2 ON T1.course_id = T2.course_id GROUP BY T1.course_id HAVING COUNT(*) > 4` (wrong_result)

### uni-06:ru (medium)

> Сколько студентов в каждой группе? Выведи группу и количество.

- эталон: `SELECT group_name, COUNT(*) FROM students GROUP BY group_name`
- base: `SELECT GROUP_NAME, COUNT(DISTINCT STUDENT_ID) AS STUDENT_COUNT FROM ENROLLMENTS GROUP BY GROUP_NAME` (schema_error)
- lora: `SELECT T2.group_name, COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id GROUP BY T2.group_name` (schema_error)

### uni-10:en (medium)

> List the names of students who received a grade of 2 at least once.

- эталон: `SELECT DISTINCT s.name FROM students s JOIN enrollments e ON e.student_id = s.student_id WHERE e.grade = 2`
- base: `SELECT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE e.grade >= 2` (wrong_result)
- lora: `SELECT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.grade >= 2` (wrong_result)

### uni-10:ru (medium)

> Выведи имена студентов, которые хотя бы раз получили оценку 2.

- эталон: `SELECT DISTINCT s.name FROM students s JOIN enrollments e ON e.student_id = s.student_id WHERE e.grade = 2`
- base: `SELECT DISTINCT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE e.grade >= 2` (wrong_result)
- lora: `SELECT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.grade >= 2` (wrong_result)

### uni-12:en (hard)

> What is the average student grade for courses of each department? Show the department name and the average grade.

- эталон: `SELECT d.name, AVG(e.grade) FROM enrollments e JOIN courses c ON c.course_id = e.course_id JOIN teachers t ON t.teacher_id = c.teacher_id JOIN departments d ON d.department_id = t.department_id GROUP BY d.department_id`
- base: `SELECT d.name, AVG(e.grade) as avg_grade FROM departments d JOIN teachers t ON d.department_id = t.department_id JOIN enrollments e ON t.teacher_id = e.teacher_id GROUP BY d.name` (schema_error)
- lora: `SELECT T2.name, AVG(T1.grade) FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id JOIN departments AS T3 ON T3.department_id = T1.student_id GROUP BY T3.name` (schema_error)

### uni-12:ru (hard)

> Какой средний балл студентов по курсам каждой кафедры? Выведи название кафедры и средний балл.

- эталон: `SELECT d.name, AVG(e.grade) FROM enrollments e JOIN courses c ON c.course_id = e.course_id JOIN teachers t ON t.teacher_id = c.teacher_id JOIN departments d ON d.department_id = t.department_id GROUP BY d.department_id`
- base: `SELECT d.name AS department, AVG(s.grade) as average_grade FROM departments d JOIN teachers t ON d.department_id = t.department_id JOIN enrollments e ON t.teacher_id = e.teacher_id JOIN courses c ON e.course_id = c.course_id GROUP BY d.name` (schema_error)
- lora: `SELECT T2.department_id, AVG(T1.grade), T2.name FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id JOIN departments AS T3 ON T3.department_id = T2.department_id GROUP BY T3.department_id` (schema_error)

### uni-13:en (hard)

> List the names of students whose average grade is above 4.5.

- эталон: `SELECT s.name FROM students s JOIN enrollments e ON e.student_id = s.student_id GROUP BY s.student_id HAVING AVG(e.grade) > 4.5`
- base: `SELECT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE AVG(e.grade) > 4.5` (syntax_error)
- lora: `SELECT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE T2.grade > 4.5 GROUP BY T1.student_id` (wrong_result)

### uni-13:ru (hard)

> Выведи имена студентов, у которых средний балл выше 4.5.

- эталон: `SELECT s.name FROM students s JOIN enrollments e ON e.student_id = s.student_id GROUP BY s.student_id HAVING AVG(e.grade) > 4.5`
- base: `SELECT s.name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE e.grade > 4.5` (wrong_result)
- lora: `SELECT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id WHERE AVG(T2.grade) > 4.5` (syntax_error)

### uni-14:ru (medium)

> Выведи имена преподавателей, которые не ведут ни одного курса.

- эталон: `SELECT name FROM teachers WHERE teacher_id NOT IN (SELECT teacher_id FROM courses WHERE teacher_id IS NOT NULL)`
- base: `SELECT DISTINCT t1.name FROM teachers AS t1 JOIN enrollments AS en ON t1.teacher_id = en.teacher_id WHERE en.course_id IS NULL` (schema_error)
- lora: `SELECT T1.name FROM teachers AS T1 JOIN courses AS T2 ON T1.teacher_id = T2.teacher_id WHERE T2.course_id IS NULL` (wrong_result)

### uni-15:en (medium)

> How many students enrolled each year? Show the year and the count, sorted by year.

- эталон: `SELECT enrollment_year, COUNT(*) FROM students GROUP BY enrollment_year ORDER BY enrollment_year`
- base: `SELECT YEAR(enrollments.enrollment_year) AS 'enrollment_year', COUNT(*) AS 'num_students' FROM enrollments GROUP BY YEAR(enrollments.enrollment_year) ORDER BY YEAR(enrollments.enrollment_year)` (schema_error)
- lora: `SELECT T1.enrollment_year, COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id GROUP BY T1.enrollment_year ORDER BY T1.enrollment_year` (wrong_result)

### uni-15:ru (medium)

> Сколько студентов поступило в каждом году? Выведи год и количество, отсортировав по году.

- эталон: `SELECT enrollment_year, COUNT(*) FROM students GROUP BY enrollment_year ORDER BY enrollment_year`
- base: `SELECT YEAR(enrollments.enrollment_year) AS year, COUNT(students.student_id) AS count FROM enrollments JOIN students ON enrollments.student_id = students.student_id GROUP BY year ORDER BY year` (schema_error)
- lora: `SELECT T1.enrollment_year, COUNT(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id GROUP BY T1.enrollment_year ORDER BY T1.enrollment_year` (wrong_result)

### uni-19:ru (medium)

> Выведи названия курсов, на которые не записан ни один студент.

- эталон: `SELECT title FROM courses WHERE course_id NOT IN (SELECT course_id FROM enrollments)`
- base: `SELECT DISTINCT c.title FROM courses AS c JOIN enrollments AS e ON c.course_id = e.course_id WHERE e.student_id IS NULL` (wrong_result)
- lora: `SELECT T1.title FROM courses AS T1 JOIN enrollments AS T2 ON T1.course_id = T2.course_id WHERE NOT EXISTS (SELECT * FROM students AS T3 WHERE T3.student_id = T2.student_id)` (wrong_result)
