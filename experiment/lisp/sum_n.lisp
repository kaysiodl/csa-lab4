(print "Enter N:")
(var n (read))

(var i 1)
(var sum 0)

(while (< i (+ n 1))
  (set sum (+ sum i))
  (set i (+ i 1))
)

(print "Sum is:")
(print sum)