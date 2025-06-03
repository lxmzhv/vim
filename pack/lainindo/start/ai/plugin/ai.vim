" Name: AI query
" Description: A plugin to modify current file using AI
" Usage: :Ai YOUR QUERY
" Created: 2025-06-01

if exists("g:ai_query_plugin_loaded")
    finish
endif

let g:ai_query_plugin_loaded = 1


" --- Configuration ---

" Define a default value if the user doesn't set it
if !exists('g:ai_query_command')
    let s:ai_plugin_root = expand('<sfile>:p:h:h') " Go from .../ai/autoload/ai.vim to .../ai
    let g:ai_query_command = 'python3 ' . s:ai_plugin_root . '/python/gemini.py'
endif

if !exists('g:ai_query_agent_instructions')
    let g:ai_query_agent_instructions =
        \ 'You are an expert software developer. Please modify the following ' .
        \ 'code according to the instructions of the user. Return ONLY the ' .
        \ 'modified code. Do not include anything else.'
endif

" --- Command Definition ---
command! -nargs=1 Ai call s:RunAiQuery(<q-args>)

" --- Main Plugin Function ---
function! s:RunAiQuery(query)
    " 1. Get the content of the current buffer
    let l:current_buffer_lines = getline(1, '$')

    " 2. Create a temporary file for the input with the original file
    "    extension, so that it's easier for LLM to get MIME type of the file.
    let l:temp_input_file = tempname() . "." . expand("%:e") 
    call writefile(l:current_buffer_lines, l:temp_input_file)

    " 3. Construct the command.
    "    Ensure proper shell escaping for the parameters.
    let l:cli_tool_command = expand(g:ai_query_command) " Expand ~ if present

    "if !executable(l:cli_tool_command)
    "    echohl ErrorMsg
    "    echo "Error: CLI tool not found or not executable at " . l:cli_tool_command
    "    echohl None
    "    call delete(l:temp_input_file)
    "    return
    "endif

    let l:escaped_query = shellescape(a:query)
    let l:escaped_input_file = shellescape(l:temp_input_file)
    let l:escaped_agent_instructions = shellescape(g:ai_query_agent_instructions)

    let l:command_to_run = l:cli_tool_command . ' -m ' . l:escaped_query . ' -i ' .
        \ l:escaped_input_file .  ' -I ' . l:escaped_agent_instructions

    " 4. Execute the command and get its output
    echom "Running: " . l:command_to_run
    let l:output = system(l:command_to_run)
    let l:exit_code = v:shell_error

    " Clean up the temporary input file
    call delete(l:temp_input_file)

    if l:exit_code != 0
        echohl ErrorMsg
        echo "Error executing CLI tool. Exit code: " . l:exit_code
        if !empty(l:output)
            echo "Output:"
            echo l:output
        endif
        echohl None
        return
    endif

    if empty(l:output)
        echom "CLI tool returned no output."
        return
    endif

    " 5. Put the output into a new vim buffer
    let l:original_bufnr = bufnr('%')
    let l:original_filetype = &filetype

    " Create a new scratch buffer
    vnew
    setlocal buftype=nofile
    setlocal bufhidden=hide
    setlocal noswapfile
    setlocal nomodified " Start with an unmodified buffer
    if !empty(l:original_filetype)
        execute 'setlocal filetype=' . l:original_filetype
    endif

    " Insert the output
    call append(0, split(l:output, "\n"))

    " Remove the initial empty line if append created one above the content
    0delete

    " Set the new buffer as unmodified initially
    setlocal nomodified

    " 6. Open a diff between the current (original) buffer and the new one
    " Go back to the original window/buffer temporarily to set it up for diff
    execute l:original_bufnr . 'windo diffthis'

    " Now, in the new buffer's window, set it to diff with the original
    " Go to the previous window (which should be the new one if vnew was successful)
    wincmd p
    windo diffthis
endfunction
