(var x 4)
(var i 0)
(var result 0)

(while (< i x)
  (set result (+ result x))
  (set i (+ i 1))
)

(print result)