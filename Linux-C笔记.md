# Linux-C笔记
## C语言中结构体成员变量前的点的作用
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