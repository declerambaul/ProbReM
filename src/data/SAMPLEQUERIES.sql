SELECT A.Aa,COUNT(*) FROM A GROUP BY A.Aa;

SELECT C.Ca,A.Aa,COUNT(*) FROM A,AC,C WHERE C.c_id=AC.c_id AND AC.a_id=A.a_id GROUP BY C.Ca,A.Aa;


SELECT D.Da,AGG_Aa,COUNT(*) FROM D,Aa_Da WHERE  Aa_Da.d_id=D.d_id GROUP BY D.Da,AGG_Aa
SELECT B.Ba,AGG_Aa,COUNT(*) FROM B,Aa_Ba WHERE  Aa_Ba.b_id=B.b_id GROUP BY B.Ba,AGG_Aa

with two parents:
SELECT C.Ca,A.Aa,AGG_Da, COUNT(*) FROM A,AC,C,Da_Ca WHERE C.c_id=AC.c_id AND AC.a_id=A.a_id AND C.c_id=Da_Ca.c_id GROUP BY C.Ca,A.Aa,AGG_Da;


SELECT B.b_id, ROUND(AVG(A.Aa)) as AGG_Aa,ROUND(AVG(C.Ca)) as AGG_Ca FROM B,AB,A,AC,C WHERE AB.b_id=B.b_id AND AB.a_id=A.a_id AND  AC.a_id=A.a_id AND AC.c_id=C.c_id GROUP BY B.b_id









------------------------------------------------------------------------------------------


SELECT rates.user_id,Categories.categories_id,rates.rating 
FROM Categories,has_category,Item,rates 
WHERE 
Categories.categories_id=has_category.categories_id AND 
Item.item_id=has_category.item_id AND 
Item.item_id=rates.item_id AND
Item.item_id=1139
;

SELECT Categories.categories_id,Categories.category_name FROM Categories,has_category,Item
WHERE 
Categories.categories_id=has_category.categories_id AND 
Item.item_id=has_category.item_id AND 
Item.item_id=1139;


SELECT Categories.categories_id,rates.rating,COUNT(*) 
FROM Categories,has_category,Item,rates 
WHERE 
Categories.categories_id=has_category.categories_id AND
Item.item_id=has_category.item_id AND
Item.item_id=rates.item_id
GROUP BY Categories.categories_id,rates.rating;


SELECT Categories.category_name,Item.title,AVG(rates.rating)
FROM Categories,has_category,Item,rates 
WHERE 
Categories.categories_id=has_category.categories_id AND
Item.item_id=has_category.item_id AND
Item.item_id=rates.item_id AND
Item.item_id<100
GROUP BY Categories.categories_id,Item.item_id;


SELECT Item.title,COUNT(*) FROM Item,rates
WHERE Item.item_id=rates.item_id AND Item.item_id<100  GROUP BY Item.item_id;
SELECT Item.title,AVG(rates.rating) FROM Item,rates
WHERE Item.item_id=rates.item_id AND Item.item_id<100  GROUP BY Item.item_id;


SELECT rates.item_id,rates.user_id, AVG(Categories.categories_id)
FROM Categories,has_category,Item,rates 
WHERE 
rates.item_id = 96 AND
rates.user_id = 831 AND
Categories.categories_id=has_category.categories_id AND
Item.item_id=has_category.item_id AND
Item.item_id=rates.item_id
GROUP BY rates.item_id,rates.user_id;