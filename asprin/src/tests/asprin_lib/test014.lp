% asprin test014.lp 0
% SATISFIABLE

1 { a(X) : dom(X) } 2.
dom(1..3).
#show a/1.

#preference(p(1),subset){
  a(X)
}.
#preference(p(2),superset){
  a(X)
} : X=3.
#preference(p(3),superset){
  a(1) & a(2) & not not a(3)
}.
#preference(q,lexico){
  -X :: **p(X)
}.
#preference(r,and){
  **p(X)
}.
#optimize(r).

%asprin version 3.0.0
%Reading from tests/asprin_lib/test014.lp
%Solving...
%Answer: 1
%a(1) a(2)
%OPTIMUM FOUND
%Answer: 2
%a(1)
%OPTIMUM FOUND
%Answer: 3
%a(2)
%OPTIMUM FOUND
%Answer: 4
%a(2) a(3)
%OPTIMUM FOUND
%Answer: 5
%a(3)
%OPTIMUM FOUND
%Answer: 6
%a(1) a(3)
%OPTIMUM FOUND
%
%Models       : 6
%  Optimum    : yes
%    Optimal    : 6
%    Calls        : 19
%    Time         : 0.132s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
%    CPU Time     : 0.128s
