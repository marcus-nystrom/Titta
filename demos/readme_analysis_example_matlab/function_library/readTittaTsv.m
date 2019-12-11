function [out,header] = readTittaTsv(datafile,columns)

fid = fopen(datafile,'rt');
a = fread(fid,'*char').';
fclose(fid);
a = regexp(a,'\r*\n','split');
if isempty(a{end})
    % remove empty line at end
    a(end) = [];
end

% split each line on tabs
a = regexp(a,'\t','split');
header = a{1};
if isempty(header{1})
    % give name to unnamed first column
    header{1} = 'sampIdx';  % 0-based
end
a = cat(1,a{2:end});        % skip header here, we just split that off

% use header to see which columns to keep
[qColKeep,i] = ismember(header,columns);

% remove shit coumns we don't need
header(~qColKeep) = [];
a(:,~qColKeep)    = [];
i(~qColKeep)      = [];

% recode i so it is strictly continuous in contained values (no gaps). this
% in case we request columns that are not in the file
[~,~,i] = unique(i);

% order in order of columns input
header(i) = header;
a(:,i)    = a;

% turn text into numbers (there is no non-number stuff in these files)
% deal specially with timestamps into numbers
qTime       = ~cellfun(@isempty,strfind(header,'time_stamp')); %#ok<STRCLFH>
for p=1:length(header)
    if qTime(p)
        out.(header{p}) = cellfun(@(x)sscanf(x,'%ld'),a(:,p));
    else
        out.(header{p}) = str2double(a(:,p));
    end
end
