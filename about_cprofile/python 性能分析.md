###使用：
#### 直接运行脚本
1. python -m cProfile -o newstats [cmd] 指定输出，不指定就到标准输出
#### 模块中使用
1. 

	```
		profiler = cProfile.Profile()
		profiler.runcall(work.work) 
		profiler.create_stats()
		profiler.dump_stats('filename')
	```	
	
2.  

	```
		cProfile.runctx('foo(5)', globals(), locals(), filename='/tmp/get_host1')
	```	

3.  

	```
		profiler = cProfile.Profile()
		cProfile.runctx('foo(5)', globals(), locals())
		profiler.create_stats()
		profiler.dump_stats('filename')
	```	
	
#### 图形化
1. windows
	1. pip install SnakeViz
	2. snakeviz program.prof
	3. snakeviz generate_parameters_f6269a2a38154664a8251176c6d5064c.stats -H 172.16.2.56 -p 8888 -s 不打开浏览器
2. linux 
    1. gprof2dot -f pstats output.pstats | dot -Tpng -o output.png 转化成图的形式

#### 结合cprofile调试Django
1.	在中间件中加入 `box_dashboard.middleware.ProfilerMiddleware`
2.	将用户的权限改成 staff
3.	在访问后的url 加入参数 ?prof 或者 ?prof&download
