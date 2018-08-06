#### python 性能分析 
1. python -m cProfile -o newstats [cmd] 指定输出，不指定就到标准输出

##### 使用：
2. import pstats
	p = pstats.Stats(file_name)
	print(p.strip_dirs().sort_stats('tottime').print_stats(15))
3. from xdashboard.handle.home import getStatusList_debug as foo
4. import cProfile
5. cProfile.runctx('foo(5)', globals(), locals())
6. cProfile.runctx('foo(5)', globals(), locals(), filename='/tmp/get_host1')
7. python manage.py shell --settings="testss"

#### 图形化
1. windows
	1. pip install SnakeViz
	2. snakeviz program.prof
2. linux 
    1. gprof2dot -f pstats output.pstats | dot -Tpng -o output.png 转化成图的形式

#### 结合cprofile调试Django
1.	在中间件中加入 `box_dashboard.middleware.ProfilerMiddleware`
2.	将用户的权限改成 staff
3.	在访问后的url 加入参数 ?prof 或者 ?prof&download
