#include<stdio.h>
#include "quicklz.h"



int qlz_mblk_compress(char *blk_buffer, char *out_buffer, int blocks_len[], int cmp_stat[], int size, int orgSize){
	// out_buffer 需要比原始大小大一块 
  	int i=0;
  	int out_offset = 0;
    int newSize=0;
    qlz_state_compress	state_compress;
  	for(;i<size;i++){
		memset(&state_compress, 0, sizeof(qlz_state_compress));
		newSize = qlz_compress(blk_buffer + i * orgSize, out_buffer+out_offset, orgSize, (qlz_state_compress *)&state_compress);
		if (newSize < orgSize){ // 如果压缩后的长度大于等于64k，则认为压缩失败，拷贝原始数据 
			cmp_stat[i] = 1;
		}
		else {
			memcpy(out_buffer+out_offset, blk_buffer + i * orgSize,  orgSize);
			newSize = orgSize;
			cmp_stat[i] = 0;
		}
		blocks_len[i] = newSize;
		out_offset += newSize;
	}  
	return 0;
}



main()
{	
	int i=0;
	char a[128 * 1024]= {0};
	char out[128*1024 + 64*1024] = {0};
	int lens[2] = {0};
	int cmp_stat[2] = {0};
	int j=0; 
	FILE *fp = NULL;
	fp = fopen("./oblk.bin", "wb");
	strcpy(a, "bcxdasdzzzzzzzzzzzzzzzzzzzzzzzzzzadsadsadasda1232312xasxa");
	qlz_mblk_compress(a, out, lens, cmp_stat, 2, 64 * 1024);
	for (;i<2;i++){
		printf("block %d len %d stat %d \n", i, lens[i], cmp_stat[i]);
		j=0;
		while(j<lens[i]){
		 	fprintf(fp,"%c",out[j++]);
		}
	}
	fclose(fp);
	
}
