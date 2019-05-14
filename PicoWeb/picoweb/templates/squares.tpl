{% args req %}
<html>
Request path: '{{req.path}}'<br>
<table border="1">
{% for i in range(5) %}
<tr><td> {{i}} </td><td> {{"%2d" % i ** 2}} </td></tr>
{% endfor %}
</table>
</html>
