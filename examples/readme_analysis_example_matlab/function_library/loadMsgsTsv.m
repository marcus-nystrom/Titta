function msgs = loadMsgsTsv(fname)

msgs = fileread(fname);
% get relevant columns
msgs = regexp(msgs,'\r*\n','split');
if isempty(msgs{end})
    % remove empty line at end
    msgs(end) = [];
end
msgs = regexp(msgs(2:end),'\t','split');
msgs = cat(1,msgs{:});
msgs(:,1) = [];
% turn timestamps into numbers
msgs(:,1) = cellfun(@(x)sscanf(x,'%ld'),msgs(:,1),'uni',false);