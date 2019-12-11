function msgs = loadMsgs(fname)

fid = fopen(fname,'rt');
msgs = textscan(fid,'%s%s','Delimiter','\t','CollectOutput',true); msgs = msgs{1};
fclose(fid);

msgs(:,1) = cellfun(@(x)sscanf(x,'%ld'),msgs(:,1),'uni',false);
