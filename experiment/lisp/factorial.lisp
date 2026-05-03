(def fact (n)
  (if (= n 0)
      1
      (* n (call fact (- n 1)))
  )
)

(print "Enter number:")
(var x (read))

(print "Factorial is:")
(print (call fact x))