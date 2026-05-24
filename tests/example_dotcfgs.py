empty_callback = '''digraph \"C_callback\" {  \nnode [shape=\"rect\"];  \n
\"141733920768\" [label = <RETURN, 5<BR/>return;> ]\n\"107374182402\" [label = <METHOD, 4<BR/>C_callback> ]\n
\"124554051586\" [label = <METHOD_RETURN, 4<BR/>void> ]\n  \"141733920768\" -> \"124554051586\" \n 
\"107374182402\" -> \"141733920768\" \n}\n'''

branching_callback = '''digraph \"&lt;lambda&gt;0\" {  \nnode [shape=\"rect\"];  \n
\"30064771110\" [label = <&lt;operator&gt;.assignment, 16<BR/>pubSelect = !pubSelect> ]\n
\"30064771107\" [label = <&lt;operator&gt;.notEquals, 14<BR/>pubSelect != 0> ]\n
\"30064771111\" [label = <&lt;operator&gt;.logicalNot, 16<BR/>!pubSelect> ]\n
\"30064771108\" [label = <put, 14<BR/>A_pub.put(&quot;example payload to A&quot;)> ]\n
\"30064771109\" [label = <put, 15<BR/>B_pub.put(&quot;example payload to B&quot;)> ]\n
\"107374182406\" [label = <METHOD, 13<BR/>&lt;lambda&gt;0> ]\n
\"124554051590\" [label = <METHOD_RETURN, 13<BR/>void> ]\n 
 \"30064771110\" -> \"124554051590\" \n  \"30064771107\" -> \"30064771108\" \n  \"30064771107\" -> \"30064771109\" \n 
\"30064771111\" -> \"30064771110\" \n  \"30064771108\" -> \"30064771111\" \n  \"30064771109\" -> \"30064771111\" \n  
\"107374182406\" -> \"30064771107\" \n}\n'''

looping_callback = '''digraph \"&lt;lambda&gt;0\" {  \nnode [shape=\"rect\"];  \n
\"30064771087\" [label = <put, 19<BR/>A_pub.put(&quot;example payload to A&quot;)> ]\n
\"30064771083\" [label = <&lt;operator&gt;.assignment, 16<BR/>i = 0> ]\n
\"30064771084\" [label = <&lt;operator&gt;.lessThan, 16<BR/>i &lt; 5> ]\n
\"30064771085\" [label = <&lt;operator&gt;.postIncrement, 16<BR/>i++> ]\n
\"30064771086\" [label = <put, 17<BR/>C_pub.put(&quot;example payload to C&quot;)> ]\n
\"107374182404\" [label = <METHOD, 15<BR/>&lt;lambda&gt;0> ]\n
\"124554051587\" [label = <METHOD_RETURN, 15<BR/>void> ]\n 
\"30064771087\" -> \"124554051587\" \n  \"30064771083\" -> \"30064771084\" \n  
\"30064771084\" -> \"30064771086\" \n  \"30064771084\" -> \"30064771087\" \n  
\"30064771085\" -> \"30064771084\" \n  \"30064771086\" -> \"30064771085\" \n  
\"107374182404\" -> \"30064771083\" \n}\n'''