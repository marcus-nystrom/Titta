function files = parseFileNames(files)

fnames  = {files.fname}.';
[~,i]   = natsortfiles(fnames);
fnames  = fnames(i);
files   = files(i);
fnames  = regexp(fnames,'_R','split');
for p=1:length(fnames)
    switch length(fnames{p})
        % ophakked trial files
        case 2
            files(p).subj    = fnames{p}{1};
            files(p).runnr   = str2double(fnames{p}{2});
    end
end
