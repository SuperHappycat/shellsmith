#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void){char line[4096];for(;;){printf("$ ");fflush(stdout);if(!fgets(line,sizeof line,stdin))return 0;line[strcspn(line,"\n")]=0;if(strncmp(line,"exit",4)==0)return atoi(line+4);printf("%s: command not found\n",line);}}
