-- ENTITIES
DROP TABLE IF EXISTS Student;
CREATE TABLE Student
(
student_id INTEGER PRIMARY KEY,
success INTEGER NOT NULL
);
DROP TABLE IF EXISTS Professor;
CREATE TABLE Professor
(
professor_id INTEGER PRIMARY KEY,
fame INTEGER NOT NULL,
funding INTEGER NOT NULL
);
-- RELATIONSHIPS
DROP TABLE IF EXISTS advisor;
CREATE TABLE advisor
(
student_id INTEGER NOT NULL,
professor_id INTEGER NOT NULL,
exist INTEGER NOT NULL,
FOREIGN KEY (student_id) REFERENCES A(student_id),
FOREIGN KEY (professor_id) REFERENCES B(professor_id),
PRIMARY KEY (student_id, professor_id)
);
