function [list,header] = readNumericFile(name, cols, nHeaderLines)

% Deze functie leest tabgescheiden kolom text files
% de getallen worden naar float geconverteerd
% het gaat mis als de file andere dingen dan getallen bevat
% alleen Nan (not a number) and inf worden geaccepteerd

header = '';

fid         = fopen(name,'rt');

if nargin>2
    if nargout>1
        for p=1:nHeaderLines
            header = [header fgets(fid)];
        end
    else
        for p=1:nHeaderLines
            fgets(fid);
        end
    end
end

str         = fread(fid,inf,'*char');
              fclose(fid);
list        = sscanf(str','%f');

if nargin>1
    assert(mod(length(list),cols)==0,'Number of columns in file not as expected (perhaps the file is not complete?). Got %d elements from file',length(list))
    list = reshape(list,cols,[]).';
end