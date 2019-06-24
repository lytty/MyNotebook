# Linux-C笔记
## 1. C语言中结构体成员变量前的点的作用
- 结构体中成员变量前的点： 结构体成员指定初始化
1. 该结构体要先定义 
2. 一个成员变量赋值完后用逗号而不是分号 
3. 初始化语句的元素以固定的顺序出现，和被初始化的数组或结构体中的元素顺序一样，这样可以不用按顺序初始化 
4. C99才开始支持的
    ```
    #include "stdio.h"
    struct student{
        int year;
        int ID; 
    };

    int main(void)
    {
        struct student s1 = {2017,1111};
        
        struct student s2 = {2222,2018};
        
        struct student s3 ={
        .year = 2019, 
        .ID = 3333}; 
    }
    ```



## 2. C语言中`#`和`##`含义

- `#`符号把一个符号直接转换为字符串，例如：

  ```c
  #define STRING(x)
  const char *str = STRING( test_string ); //str的内容就是"test_string"，也就是说#会把其后的符号
  ```

- ##符号会连接两个符号，从而产生新的符号(词法层次)，例如：

  ```c
  #define SIGN( x ) INT_##x
  int SIGN( 1 ); //宏被展开后将成为：int INT_1;
  ```

- 变参宏，这个比较酷，它使得你可以定义类似的宏：

  ```c
  #define LOG( format, ... ) printf( format, __VA_ARGS__ )
  LOG( "%s %d", str, count ); //__VA_ARGS__是系统预定义宏，被自动替换为参数列表。
  ```

- 当一个宏自己调用自己时，会发生什么？例如：

  ```c
  #define TEST( x ) ( x + TEST( x ) )
  ```

  ​		TEST( 1 ); 会发生什么？为了防止无限制递归展开，语法规定，当一个宏遇到自己时，就停止展开，也就是说，当对TEST( 1 )进行展开时，展开过程中又发现了一个TEST，那么就将这个TEST当作一般的符号。TEST(1)最终被展开为：1 + TEST( 1) 。